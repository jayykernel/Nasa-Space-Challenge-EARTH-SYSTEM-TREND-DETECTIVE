"""NOAA GSOM station precipitation acquisition and durable raw JSON receipt."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.connectors.noaa import NoaaCDOConnector
from app.models.schemas import AcquisitionResult
from app.storage import jobs
from app.storage.files import checksum


async def acquire(request, investigation_id: str) -> tuple[AcquisitionResult, list[dict]]:
    connector = NoaaCDOConnector()
    time_range = request.time_range.model_dump(mode="json")
    stations = await connector.discover_stations(request.geometry, time_range["start"], time_range["end"])
    if not stations:
        raise RuntimeError("NOAA CDO returned no GHCN monthly precipitation stations inside the selected region and date range")
    observations = await connector.retrieve_monthly([station["id"] for station in stations], time_range["start"], time_range["end"])
    if not observations:
        raise RuntimeError("NOAA CDO found stations but returned no monthly precipitation observations for this request")

    folder = (jobs.DATA_ROOT / "raw" / "noaa" / investigation_id).resolve()
    folder.relative_to(jobs.DATA_ROOT.resolve())
    folder.mkdir(parents=True, exist_ok=True)
    raw_path = folder / "gsom-monthly-precipitation.json"
    document = {"provider": "noaa_cdo", "dataset": connector.dataset_id, "datatype": connector.datatype_id,
                "units_requested": "metric", "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "stations": stations, "observations": observations}
    raw_path.write_text(json.dumps(document, separators=(",", ":"), allow_nan=False), encoding="utf-8")
    validation = {"path": str(raw_path), "size_bytes": raw_path.stat().st_size, "sha256": checksum(raw_path)}
    result = AcquisitionResult(
        investigation_id=investigation_id, provider="noaa", dataset_id="noaa_ghcn_monthly_precipitation",
        product_version="CDO v2 / GSOM", status="completed", raw_files=[str(raw_path)], raw_format="JSON",
        requested_variable=request.variable, requested_time_range=request.time_range, requested_geometry=request.geometry,
        source_metadata={"catalog": "NOAA Climate Data Online API v2", "dataset_id": connector.dataset_id,
                         "datatype_id": connector.datatype_id, "datatype": "Monthly precipitation total",
                         "station_count": len(stations), "stations": [{"id": s["id"], "name": s.get("name"),
                            "latitude": s["latitude"], "longitude": s["longitude"],
                            "mindate": s.get("mindate"), "maxdate": s.get("maxdate")} for s in stations]},
        acquisition_metadata={"observation_count": len(observations), "validated_files": [validation]},
    )
    return result, [validation]
