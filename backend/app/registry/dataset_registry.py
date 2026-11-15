"""Dataset registry: declarative catalog metadata only; no I/O or processing."""
from app.models.schemas import DatasetInfo

DATASET_REGISTRY: dict[str, dict] = {
    "gpm_imerg_monthly": {
        "feature_id": "gpm_imerg_monthly",
        "display_name": "GPM IMERG Final Precipitation L3 Monthly",
        "mission": "Global Precipitation Measurement (GPM)",
        "dataset_short_name": "GPM_3IMERGM",
        "collection_id": "GPM_3IMERGM",
        "version": "07",
        "variable_name": "precipitation",
        "units": "mm/hr (monthly mean rate; checked against source attributes)",
        "spatial_resolution": "0.1° × 0.1°",
        "temporal_resolution": "Monthly",
        "historical_coverage": "2000-06 to 2025-09 in the currently available V07B archive",
        "authentication_required": True,
        "access_endpoint": "NASA CMR / Earthdata Login via earthaccess",
        "processing_notes": "Uses catalog-discovered granules. Units and variable metadata are read from each source file.",
        "description": "GPM IMERG Final Run monthly precipitation estimate, V07.",
        "acquisition_status": "implemented",
        "provider": "earthdata",
        "format": "HDF5",
        "pipeline": "earthdata_pipeline",
    },
    "noaa_ghcn_monthly_precipitation": {
        "feature_id": "noaa_ghcn_monthly_precipitation",
        "display_name": "NOAA GHCN Monthly Precipitation",
        "mission": "Global Historical Climatology Network",
        "dataset_short_name": "GSOM",
        "collection_id": "GSOM",
        "version": "CDO v2",
        "variable_name": "PRCP",
        "units": "mm/month",
        "spatial_resolution": "Station network; varies by region",
        "temporal_resolution": "Monthly station observations",
        "historical_coverage": "Station-specific; queried from NOAA CDO",
        "authentication_required": True,
        "access_endpoint": "NOAA Climate Data Online API v2",
        "processing_notes": "Monthly station totals are averaged across stations inside the selected geometry; station observations are not a gridded satellite product.",
        "description": "NOAA GHCN Global Summary of the Month precipitation observations from stations inside the selected region.",
        "acquisition_status": "implemented",
        "provider": "noaa",
        "format": "JSON",
        "pipeline": "noaa_pipeline",
    },
}

def get_dataset(dataset_id: str) -> dict | None:
    return DATASET_REGISTRY.get(dataset_id)

def list_datasets() -> list[DatasetInfo]:
    return [DatasetInfo(**{k: v for k, v in item.items() if k in DatasetInfo.model_fields}) for item in DATASET_REGISTRY.values()]
