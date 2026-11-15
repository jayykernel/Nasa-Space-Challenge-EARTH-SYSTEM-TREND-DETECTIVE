"""Normalize NOAA CDO monthly station JSON into the common time-series model."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr

from app.normalization.common_model import NormalizedDataset


def load_noaa_files(paths: list[str], variable: str) -> NormalizedDataset:
    documents = [json.loads(Path(path).read_text(encoding="utf-8")) for path in paths]
    stations_by_id = {station["id"]: station for doc in documents for station in doc["stations"]}
    observations = [row for doc in documents for row in doc["observations"]]
    station_ids = sorted({row.get("station") for row in observations if row.get("station") in stations_by_id})
    months = sorted({pd.Timestamp(row["date"]).to_period("M").to_timestamp() for row in observations if row.get("date")})
    if not station_ids or not months:
        raise ValueError("NOAA CDO returned no usable station/month precipitation values")
    station_lookup = {station_id: index for index, station_id in enumerate(station_ids)}
    month_lookup = {month.strftime("%Y-%m"): index for index, month in enumerate(months)}
    values = np.full((len(months), len(station_ids)), np.nan, dtype=np.float32)
    duplicates: dict[tuple[int, int], list[float]] = {}
    for row in observations:
        station_id = row.get("station")
        if station_id not in station_lookup or row.get("value") is None:
            continue
        try:
            value = float(row["value"])
            if not np.isfinite(value) or value < 0:
                continue
            month_key = pd.Timestamp(row["date"]).strftime("%Y-%m")
            key = (month_lookup[month_key], station_lookup[station_id])
            duplicates.setdefault(key, []).append(value)
        except (ValueError, KeyError, TypeError):
            continue
    for (month_index, station_index), samples in duplicates.items():
        values[month_index, station_index] = float(np.mean(samples))
    stations = [stations_by_id[key] for key in station_ids]
    da = xr.DataArray(values, dims=("time", "station"),
        coords={"time": pd.DatetimeIndex(months), "station": station_ids,
                "lat": ("station", [float(s["latitude"]) for s in stations]),
                "lon": ("station", [float(s["longitude"]) for s in stations])},
        name=variable, attrs={"units": "mm/month", "original_units": "mm/month",
                              "provider": "noaa", "dataset_id": "noaa_ghcn_monthly_precipitation",
                              "source_variable": "PRCP", "crs": "EPSG:4326",
                              "aggregation_semantics": "monthly precipitation accumulation"})
    station_metadata = [{"id": s["id"], "name": s.get("name"), "latitude": s["latitude"], "longitude": s["longitude"]} for s in stations]
    return NormalizedDataset(da, variable, "mm/month", "noaa", "noaa_ghcn_monthly_precipitation",
        {"stations": station_metadata, "raw_record_count": len(observations)}, "mm/month")
