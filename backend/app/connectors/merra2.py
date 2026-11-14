"""Connector for MERRA-2 Monthly Single-Level Diagnostics."""
import os
import httpx
import base64
import time
from typing import List, Dict, Any
from datetime import datetime
from app.connectors.base import BaseConnector
from app.registry.datasets import get_dataset_info
from app.processing.spatial import get_grid_cell_areas

class MERRA2Connector(BaseConnector):
    """Connector for MERRA-2 Monthly Single-Level Diagnostics."""

    VARIABLE_MAP = {
        "temperature": "T2M",
        "specific_humidity": "QV2M",
        "relative_humidity": "RH2M",
    }

    UNIT_CONVERSIONS = {
        "temperature": {"from": "K", "to": "°C", "factor": 1, "offset": -273.15},
        "specific_humidity": {"from": "kg/kg", "to": "kg/kg", "factor": 1, "offset": 0},
        "relative_humidity": {"from": "%", "to": "%", "factor": 1, "offset": 0},
    }

    def __init__(self, variable: str):
        dataset_map = {
            "temperature": "merra2_temperature",
            "specific_humidity": "merra2_specific_humidity",
            "relative_humidity": "merra2_relative_humidity",
        }
        super().__init__(dataset_map.get(variable, "merra2_temperature"))
        self.variable = variable
        self.merra2_var = self.VARIABLE_MAP.get(variable, "T2M")
        self.base_url = "https://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2TMNXSLV.5.12.4/"
        self.session = None

    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with NASA Earthdata using basic auth."""
        self.auth_token = f"{username}:{password}"
        return True

    async def discover(
        self,
        geometry: Dict[str, Any],
        time_range: Dict[str, str],
        variable: str
    ) -> List[Dict[str, Any]]:
        """Discover available MERRA-2 monthly granules."""
        # Parse time range
        start_year = int(time_range["start"][:4])
        end_year = int(time_range["end"][:4])
        start_month = int(time_range["start"][5:7])
        end_month = int(time_range["end"][5:7])

        granules = []

        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                # Skip if outside exact range
                if year == start_year and month < start_month:
                    continue
                if year == end_year and month > end_month:
                    continue

                # MERRA-2 monthly file naming
                filename = f"MERRA2_400.tavgM_2d_slv_Nx.{year}{month:02d}.nc4"
                url = f"{self.base_url}{year}/{filename}"

                granules.append({
                    "filename": filename,
                    "url": url,
                    "year": year,
                    "month": month,
                    "start_time": f"{year}-{month:02d}-01T00:00:00Z",
                    "end_time": f"{year}-{month:02d}-28T23:59:59Z",
                    "size_bytes": 150000000,  # ~150 MB
                })

        return granules

    async def retrieve(
        self,
        granules: List[Dict[str, Any]],
        output_dir: str
    ) -> List[str]:
        """Download MERRA-2 granules to local files."""
        os.makedirs(output_dir, exist_ok=True)
        local_files = []

        async with httpx.AsyncClient(timeout=600.0) as client:
            for granule in granules:
                local_path = os.path.join(output_dir, granule["filename"])

                # Check if already downloaded
                if os.path.exists(local_path):
                    local_files.append(local_path)
                    continue

                try:
                    headers = {}
                    if self.auth_token:
                        auth_header = base64.b64encode(self.auth_token.encode()).decode()
                        headers["Authorization"] = f"Basic {auth_header}"

                    response = await client.get(granule["url"], headers=headers)
                    response.raise_for_status()

                    with open(local_path, "wb") as f:
                        f.write(response.content)

                    local_files.append(local_path)
                except Exception as e:
                    print(f"Failed to download {granule['url']}: {e}")

        return local_files

    async def inspect_metadata(self, file_path: str) -> Dict[str, Any]:
        """Inspect MERRA-2 NetCDF file metadata."""
        metadata = {"error": None}
        try:
            import xarray as xr
            ds = xr.open_dataset(file_path)
            metadata["variables"] = list(ds.data_vars)
            metadata["dimensions"] = dict(ds.dims)
            metadata["coords"] = list(ds.coords)
            metadata["attrs"] = dict(ds.attrs)

            if self.merra2_var in ds.data_vars:
                var = ds[self.merra2_var]
                metadata[f"{self.merra2_var}_shape"] = var.shape
                metadata[f"{self.merra2_var}_attrs"] = dict(var.attrs)

            ds.close()
        except Exception as e:
            metadata["error"] = str(e)

        return metadata

    def normalize(self, data: Any, variable: str) -> Any:
        """Normalize MERRA-2 variables to standard units."""
        if isinstance(data, dict) or isinstance(data, str):
            return data

        if self.merra2_var in self.UNIT_CONVERSIONS:
            conv = self.UNIT_CONVERSIONS[self.merra2_var]
            normalized = data * conv["factor"] + conv["offset"]
            normalized.attrs["units"] = conv["to"]
            normalized.attrs["original_units"] = conv["from"]
            if conv["offset"] != 0:
                normalized.attrs["conversion"] = f"multiplied by {conv['factor']} and added {conv['offset']}"
            else:
                normalized.attrs["conversion"] = f"multiplied by {conv['factor']}"
            return normalized

        return data