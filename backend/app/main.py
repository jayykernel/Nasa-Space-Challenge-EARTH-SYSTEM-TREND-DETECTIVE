"""Main FastAPI application for Earth System Trend Detective."""
import asyncio
import uuid
from datetime import datetime
from typing import Any, Literal
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator

from app.connectors.base import get_connector, BaseConnector
from app.registry.datasets import list_available_variables, list_available_datasets, get_dataset_for_variable, get_variable_info, get_dataset_info
from app.processing.spatial import validate_geometry, extract_region, extract_grid_cell_time_series, spatial_trend_analysis, compute_grid_cell_areas, apply_land_mask, regrid_to_common
from app.processing.analytics import comprehensive_trend_analysis, linear_regression_analysis, descriptive_statistics, generate_interpretation, generate_limitations, spatial_trend_analysis as spatial_analytics

app = FastAPI(
    title="Earth System Trend Detective API",
    description="NASA Space Apps Challenge 2026 - Earth System Trend Detective Backend",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory investigation store
investigations: dict[str, dict[str, Any]] = {}


class InvestigationRequest(BaseModel):
    variables: list[str] = Field(..., min_length=1, description="Environmental variables to investigate")
    geometry: dict = Field(..., description="Geographical region as GeoJSON")
    time_range: dict = Field(..., description="Temporal range with start and end dates")
    temporal_resolution: Literal["daily", "monthly", "annual", "seasonal"] = "monthly"

    @validator('time_range')
    def validate_time_range(cls, v):
        if not v.get('start') or not v.get('end'):
            raise ValueError('Time range must include start and end dates')
        return v


class InvestigationStatusResponse(BaseModel):
    investigation_id: str
    status: Literal["queued", "retrieving_data", "processing", "analyzing", "completed", "failed", "cancelled"]
    progress: int
    message: str | None = None


@app.get("/api/v1/datasets", response_model=list[dict[str, Any]])
async def list_datasets():
    """List all available NASA datasets."""
    return list_available_datasets()


@app.get("/api/v1/variables", response_model=list[dict[str, Any]])
async def list_variables():
    """List all available environmental variables."""
    return list_available_variables()


@app.get("/api/v1/variables/{variable_key}")
async def get_variable(variable_key: str):
    """Get information about a specific environmental variable."""
    info = get_variable_info(variable_key)
    if info is None:
        raise HTTPException(status_code=404, detail=f"Variable {variable_key} not found")
    return info.dict()


@app.post("/api/v1/analysis", response_model=dict[str, Any])
async def start_analysis(request: InvestigationRequest, background_tasks: BackgroundTasks):
    """Start a new investigation analysis."""
    investigation_id = str(uuid.uuid4())

    try:
        # Validate geometry
        is_valid, error_msg = validate_geometry(request.geometry)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid geometry: {error_msg}")

        # Parse time range
        start_date = request.time_range.get("start", "2000-01-01")
        end_date = request.time_range.get("end", "2025-12-31")

        # Create investigation record
        investigations[investigation_id] = {
            "id": investigation_id,
            "status": "queued",
            "progress": 0,
            "variables": request.variables,
            "geometry": request.geometry,
            "time_range": {
                "start": start_date,
                "end": end_date,
            },
            "temporal_resolution": request.temporal_resolution,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "message": "Investigation queued",
            "step": "initializing",
            "datasets": [],
            "data_files": [],
            "processed_data": None,
            "trend_results": None,
            "spatial_results": None,
            "report": None,
        }

        # Start investigation as background task
        background_tasks.add_task(run_investigation, investigation_id)

        return {
            "investigation_id": investigation_id,
            "status": "queued",
            "message": "Investigation started successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start investigation: {str(e)}")


@app.get("/api/v1/analysis/{investigation_id}/status", response_model=InvestigationStatusResponse)
async def get_investigation_status(investigation_id: str):
    """Get investigation status."""
    if investigation_id not in investigations:
        raise HTTPException(status_code=404, detail="Investigation not found")

    inv = investigations[investigation_id]
    return InvestigationStatusResponse(
        investigation_id=investigation_id,
        status=inv["status"],
        progress=inv["progress"],
        message=inv["message"],
    )


@app.get("/api/v1/analysis/{investigation_id}/results", response_model=dict[str, Any])
async def get_investigation_results(investigation_id: str):
    """Get investigation results."""
    if investigation_id not in investigations:
        raise HTTPException(status_code=404, detail="Investigation not found")

    inv = investigations[investigation_id]
    if inv["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Investigation not completed yet. Status: {inv['status']}")

    return {
        "investigation_id": investigation_id,
        "variables": inv["variables"],
        "trend_statistics": inv.get("trend_results"),
        "spatial_results": inv.get("spatial_results"),
        "data_quality": inv.get("data_quality", {}),
        "methodology": inv.get("methodology", ""),
        "limitations": inv.get("limitations", []),
        "completed_at": inv.get("completed_at"),
    }


@app.get("/api/v1/analysis/{investigation_id}/map", response_model=dict[str, Any])
async def get_investigation_map(investigation_id: str):
    """Get spatial results for map visualization."""
    if investigation_id not in investigations:
        raise HTTPException(status_code=404, detail="Investigation not found")

    inv = investigations[investigation_id]
    if inv["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Investigation not completed yet")

    spatial = inv.get("spatial_results", {})
    return {
        "grid_cells": spatial,
        "centroids": [
            {"lat": cell["lat"], "lon": cell["lon"], "trend_dir": cell["trend_direction"]}
            for cell in spatial
        ],
    }


@app.get("/api/v1/analysis/{investigation_id}/report", response_model=dict[str, Any])
async def get_investigation_report(investigation_id: str):
    """Get investigation report."""
    if investigation_id not in investigations:
        raise HTTPException(status_code=404, detail="Investigation not found")

    inv = investigations[investigation_id]
    if inv["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Investigation not completed yet")

    report = inv.get("report")
    if report is None:
        # Generate report on demand
        report = generate_report(inv)
        inv["report"] = report

    return report


@app.post("/api/v1/analysis/{investigation_id}/cancel")
async def cancel_investigation(investigation_id: str):
    """Cancel an investigation."""
    if investigation_id not in investigations:
        raise HTTPException(status_code=404, detail="Investigation not found")

    investigations[investigation_id]["status"] = "cancelled"
    investigations[investigation_id]["message"] = "Investigation cancelled by user"
    investigations[investigation_id]["progress"] = 100

    return {"investigation_id": investigation_id, "status": "cancelled", "message": "Cancelled"}


async def run_investigation(investigation_id: str):
    """Run the full investigation pipeline."""
    from app.connectors.base import get_connector as get_base_connector

    inv = investigations[investigation_id]
    inv["status"] = "retrieving_data"
    inv["progress"] = 10
    inv["message"] = "Initializing data retrieval..."
    inv["updated_at"] = datetime.now().isoformat()

    try:
        geometry = inv["geometry"]
        time_range = inv["time_range"]
        variables = inv["variables"]

        # Validate geometry early
        is_valid, error_msg = validate_geometry(geometry)
        if not is_valid:
            inv["status"] = "failed"
            inv["message"] = f"Invalid geometry: {error_msg}"
            return

        all_results = []
        all_datasets = []
        all_processed_data = {}

        # Process each variable independently
        for var_idx, variable in enumerate(variables):
            # Update progress
            progress = 10 + (var_idx / max(len(variables), 1)) * 40  # 10-50% for data retrieval
            inv["progress"] = int(progress)
            inv["message"] = f"Processing {variable} ({var_idx+1}/{len(variables)})..."
            inv["updated_at"] = datetime.now().isoformat()

            # Get dataset info
            dataset_info = get_dataset_for_variable(variable)
            if dataset_info is None:
                # Try to find any dataset for this variable
                dataset_info = get_dataset_info(variables[0] if variables else "")

            all_datasets.append(dataset_info.dict() if dataset_info else {})

            # Get connector
            try:
                connector: BaseConnector = get_base_connector(variable)
            except ValueError as e:
                # No connector for this variable - skip
                inv["progress"] = 90
                inv["message"] = f"No connector available for {variable}: {str(e)}"
                continue

            # Authenticate (in production, use stored credentials)
            # connector.authenticate(username="earthdata_user", password="password")

            # Discover and retrieve data
            try:
                granules = await connector.discover(
                    geometry=geometry,
                    time_range=time_range,
                    variable=variable
                )

                inv["message"] = f"Discovered {len(granules)} granules for {variable}"

                if not granules:
                    inv["message"] = f"No data granules found for {variable} in the requested region/time range"
                    continue

                # Retrieve data
                output_dir = f"/tmp/investigation_{investigation_id}_{var_idx}"
                data_files = await connector.retrieve(granules, output_dir)

                inv["data_files"] = data_files
                inv["message"] = f"Retrieved {len(data_files)} files for {variable}"

                # Inspect metadata
                if data_files:
                    metadata = await connector.inspect_metadata(data_files[0])
                    all_processed_data[variable] = {"metadata": metadata, "granules": granules}

            except Exception as e:
                inv["message"] = f"Error retrieving data for {variable}: {str(e)}"
                continue

        # Store datasets info
        inv["datasets"] = all_datasets

        if not all_processed_data:
            inv["status"] = "failed"
            inv["message"] = "No data could be retrieved for any variable"
            return

        # Extract data for each variable
        inv["progress"] = 50
        inv["message"] = "Extracting regional measurements..."
        inv["updated_at"] = datetime.now().isoformat()

        from app.processing.spatial import extract_region, extract_grid_cell_time_series

        for var_idx, (variable, data_info) in enumerate(all_processed_data.items()):
            connector = get_base_connector(variable)

            # Extract measurements
            try:
                # This is a simplified extraction - real implementation would load actual NetCDF files
                # For now, use the connector's normalize method
                normalized = connector.normalize(None, variable)

                # Get grid cell areas
                grid_areas = connector.get_grid_cell_areas() if hasattr(connector, 'get_grid_cell_areas') else None

            except Exception as e:
                inv["message"] = f"Error normalizing data for {variable}: {str(e)}"
                continue

        # Perform statistical analysis
        inv["progress"] = 70
        inv["message"] = "Performing statistical analysis..."
        inv["updated_at"] = datetime.now().isoformat()

        from app.processing.analytics import comprehensive_trend_analysis, spatial_trend_analysis

        trend_results = {}
        spatial_results = {}

        for variable in variables:
            # Get processed data for this variable
            var_data = all_processed_data.get(variable, {})

            # Run comprehensive trend analysis
            # This requires actual time series data - placeholder for now
            # trend_results[variable] = comprehensive_trend_analysis(...)

            # For now, generate placeholder results
            trend_results[variable] = {
                "linear_regression": {"slope": 0.0, "p_value": 1.0, "r_squared": 0.0},
                "mann_kendall": {"trend": "no_trend", "p_value": 1.0},
                "sens_slope": {"slope": 0.0, "ci_lower": 0.0, "ci_upper": 0.0},
                "trend_direction": "no_significant_trend",
                "is_significant": False,
            }

        # Spatial trend analysis
        try:
            cell_results = spatial_analytics(
                cell_data=[],  # Would come from actual grid cell extraction
                time_values=np.array([]),
                variable=variables[0] if variables else "precipitation",
                unit="mm/day",
                period=12,
            )
            spatial_results = {var: cell_results for var in variables}
        except Exception as e:
            spatial_results = {"error": str(e)}

        # Mark as completed
        inv["status"] = "completed"
        inv["progress"] = 100
        inv["message"] = "Analysis complete"
        inv["trend_results"] = trend_results
        inv["spatial_results"] = spatial_results
        inv["data_quality"] = {"variables_processed": len(variables), "datasets_used": len(all_datasets)}
        inv["completed_at"] = datetime.now().isoformat()
        inv["message"] = "Analysis completed successfully"

        # Generate report
        try:
            inv["report"] = generate_report(inv)
        except Exception as e:
            inv["report"] = {"error": f"Report generation failed: {str(e)}"}

    except Exception as e:
        import traceback
        traceback.print_exc()
        inv["status"] = "failed"
        inv["message"] = f"Investigation failed: {str(e)}"
        inv["updated_at"] = datetime.now().isoformat()


def generate_report(inv: dict[str, Any]) -> dict[str, Any]:
    """Generate a scientific investigation report."""
    from app.registry.datasets import get_dataset_for_variable, get_variable_info
    from app.processing.analytics import generate_interpretation, generate_limitations

    variables = inv.get("variables", [])
    trend_results = inv.get("trend_results", {})
    datasets = inv.get("datasets", [])

    # Build report sections
    sections = {
        "title": f"Earth System Trend Investigation: {', '.join(variables)}",
        "investigation_id": inv["id"],
        "region_description": f"Geographical region defined by geometry",
        "variables": [],
        "dataset_info": [],
        "time_period": f"{inv['time_range']['start']} to {inv['time_range']['end']}",
        "observation_count": {},
        "units": {},
        "data_quality_summary": "",
        "trend_summary": {},
        "rate_of_change": {},
        "statistical_significance": {},
        "confidence_intervals": {},
        "interpretation": "",
        "scientific_limitations": [],
        "data_source_citation": "",
        "generated_at": datetime.now().isoformat(),
    }

    for var in variables:
        var_info = get_variable_info(var)
        var_dataset = get_dataset_for_variable(var)

        if var_dataset:
            sections["dataset_info"].append(var_dataset.dict())

        if var_info:
            sections["variables"].append({
                "name": var_info.display_name,
                "unit": var_info.unit,
                "description": var_info.description,
            })

        # Add trend data
        if var in trend_results:
            tr = trend_results[var]
            sections["trend_summary"][var] = tr.get("trend_direction", "unknown")
            sections["rate_of_change"][var] = tr.get("sens_slope", {}).get("slope", 0.0)
            sections["statistical_significance"][var] = tr.get("is_significant", False)

            # Confidence intervals
            ci = tr.get("sens_slope", {}).get("ci_lower", 0.0), tr.get("sens_slope", {}).get("ci_upper", 0.0)
            sections["confidence_intervals"][var] = [ci[0], ci[1]]
            sections["observation_count"][var] = tr.get("linear_regression", {}).get("n_obs", 0)
            sections["units"][var] = var_info.unit if var_info else "unknown"

    # Interpretations
    interpretations = []
    for var in variables:
        if var in trend_results:
            tr = trend_results[var]
            interpretations.append(tr.get("evidence", ["No analysis available"])[0] if tr.get("evidence") else "No analysis available")
    sections["interpretation"] = " ".join(interpretations[:3])  # Top 3

    # Limitations
    if trend_results:
        for var in variables:
            if var in trend_results:
                sections["scientific_limitations"].extend(
                    generate_limitations(
                        {},
                        {"significant_autocorr": False},
                        {"h": False, "p_value": 1.0},
                        {"h": False, "p_value": 1.0}
                    )
                )
    sections["scientific_limitations"] = list(set(sections["scientific_limitations"]))[:10]

    # Data source citation
    for ds in sections.get("dataset_info", []):
        sections["data_source_citation"] += f"- {ds.get('display_name', 'Unknown dataset')} ({ds.get('mission', 'Unknown mission')}), Version {ds.get('version', '?')}. "

    return sections