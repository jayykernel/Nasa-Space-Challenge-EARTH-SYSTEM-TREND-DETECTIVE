import asyncio
import json
from datetime import date

import numpy as np
import pandas as pd
from shapely.geometry import box, mapping

from app.acquisition import noaa_pipeline
from app.acquisition import pipeline
from app.storage import jobs


def test_noaa_monthly_station_pipeline_uses_realistic_metric_accumulations(monkeypatch, tmp_path):
    monkeypatch.setattr(jobs, "DB_PATH", tmp_path / "jobs.sqlite3")
    monkeypatch.setattr(jobs, "DATA_ROOT", tmp_path / "data")
    jobs.initialize()
    station = {"id": "GHCND:TEST0001", "name": "Fixture station", "latitude": 9.0,
               "longitude": 76.0, "mindate": "2000-01-01", "maxdate": "2025-12-01"}
    dates = pd.date_range("2000-01-01", periods=36, freq="MS")
    observations = [{"station": station["id"], "date": timestamp.strftime("%Y-%m-01T00:00:00"),
                     "datatype": "PRCP", "value": 10.0 + timestamp.month}
                    for timestamp in dates]

    async def discover(self, _geometry, _start, _end):
        return [station]

    async def retrieve(self, _station_ids, _start, _end):
        return observations

    monkeypatch.setattr(noaa_pipeline.NoaaCDOConnector, "discover_stations", discover)
    monkeypatch.setattr(noaa_pipeline.NoaaCDOConnector, "retrieve_monthly", retrieve)
    request = {"variable": "precipitation", "variables": ["precipitation"], "dataset_id": "noaa_ghcn_monthly_precipitation",
               "provider": "noaa", "geometry": mapping(box(75.5, 8.5, 76.5, 9.5)),
               "time_range": {"start": "2000-01-01", "end": "2002-12-31"}, "temporal_resolution": "monthly"}
    jobs.create("noaa-fixture", request)
    asyncio.run(pipeline.run_investigation("noaa-fixture"))
    saved = jobs.get("noaa-fixture")

    assert saved["status"] == "completed", saved["error"]
    result = saved["result"]
    assert result["data_quality"]["observation_count"] == 36
    assert result["data_quality"]["stations_used"] == 1
    assert result["units"]["precipitation"] == "mm/month"
    assert result["time_series"]["precipitation"][0]["value"] == 11.0
    assert result["trend_statistics"]["precipitation"]["sens_slope"]["slope"] > 0
    assert result["provenance"]["provider"] == "noaa"
    raw = tmp_path / "data" / "raw" / "noaa" / "noaa-fixture" / "gsom-monthly-precipitation.json"
    assert json.loads(raw.read_text(encoding="utf-8"))["observations"] == observations


def test_noaa_annual_aggregation_sums_monthly_precipitation():
    from app.processing.aggregation import aggregate

    frame = pd.DataFrame({"time": pd.date_range("2001-01-01", periods=12, freq="MS"), "value": np.full(12, 20.0)})
    annual = aggregate(frame, "annual", variable="precipitation", accumulation=True)
    assert annual.iloc[0].value == 240.0


def test_noaa_connector_requires_token_without_echoing_it(monkeypatch):
    monkeypatch.delenv("NOAA_CDO_TOKEN", raising=False)
    try:
        noaa_pipeline.NoaaCDOConnector()
    except RuntimeError as error:
        assert "NOAA_CDO_TOKEN" in str(error)
    else:
        raise AssertionError("Expected token validation")
