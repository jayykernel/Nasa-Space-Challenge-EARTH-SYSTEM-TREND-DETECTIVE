"""NOAA Climate Data Online v2 station and monthly-summary client."""
from __future__ import annotations

import asyncio
import os
from typing import Any

import httpx
from shapely.geometry import Point, shape


class NoaaCDOConnector:
    base_url = "https://www.ncei.noaa.gov/cdo-web/api/v2"
    dataset_id = "GSOM"
    datatype_id = "PRCP"

    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("NOAA_CDO_TOKEN", "")
        if not self.token:
            raise RuntimeError("NOAA CDO access requires NOAA_CDO_TOKEN in backend/.env")

    async def _get(self, client: httpx.AsyncClient, endpoint: str, params: list[tuple[str, str]]) -> dict[str, Any]:
        response = await client.get(f"{self.base_url}/{endpoint}", params=params, headers={"token": self.token})
        if response.status_code == 429:
            raise RuntimeError("NOAA CDO rate limit reached; wait before retrying this investigation")
        if response.status_code == 401:
            raise RuntimeError("NOAA CDO rejected NOAA_CDO_TOKEN; check the token in backend/.env")
        response.raise_for_status()
        return response.json()

    async def discover_stations(self, geometry: dict, start: str, end: str) -> list[dict[str, Any]]:
        region = shape(geometry)
        min_lon, min_lat, max_lon, max_lat = region.bounds
        base = [("datasetid", self.dataset_id), ("datatypeid", self.datatype_id),
                ("extent", f"{min_lat},{min_lon},{max_lat},{max_lon}"),
                ("startdate", start), ("enddate", end), ("limit", "1000")]
        output = []
        offset = 0
        async with httpx.AsyncClient(timeout=45) as client:
            while True:
                payload = await self._get(client, "stations", base + [("offset", str(offset))])
                await asyncio.sleep(0.21)
                records = payload.get("results", [])
                output.extend(record for record in records
                              if record.get("latitude") is not None and record.get("longitude") is not None
                              and region.covers(Point(record["longitude"], record["latitude"])))
                count = int(payload.get("metadata", {}).get("resultset", {}).get("count", 0))
                if not records or offset + len(records) >= count:
                    break
                offset += len(records)
        return output

    async def retrieve_monthly(self, station_ids: list[str], start: str, end: str) -> list[dict[str, Any]]:
        output = []
        async with httpx.AsyncClient(timeout=60) as client:
            for year_start in range(int(start[:4]), int(end[:4]) + 1, 10):
                year_end = min(year_start + 9, int(end[:4]))
                chunk_start = max(start, f"{year_start:04d}-01-01")
                chunk_end = min(end, f"{year_end:04d}-12-31")
                for index in range(0, len(station_ids), 10):
                    ids = station_ids[index:index + 10]
                    base = [("datasetid", self.dataset_id), ("datatypeid", self.datatype_id),
                            ("startdate", chunk_start), ("enddate", chunk_end), ("units", "metric"), ("limit", "1000")]
                    base.extend(("stationid", station_id) for station_id in ids)
                    offset = 0
                    while True:
                        payload = await self._get(client, "data", base + [("offset", str(offset))])
                        await asyncio.sleep(0.21)
                        records = payload.get("results", [])
                        output.extend(records)
                        count = int(payload.get("metadata", {}).get("resultset", {}).get("count", 0))
                        if not records or offset + len(records) >= count:
                            break
                        offset += len(records)
        return output
