"""Connector for GLDAS Noah Land Surface Model data."""
import os
import httpx
import base64
from typing import List, Dict, Any
from datetime import datetime
from app.connectors.base import BaseConnector

class GLDASConnector(BaseConnector):
    """Connector for GLDAS Noah Land Surface Model data."""

    VARIABLE_MAP = {
        "soil_moisture": "SoilMoi0_10cm_inst",
        "evapotranspiration": "Evap_tavg",
        "runoff": "Qs_tavg",
        "subsurface_runoff": "Qsb_tavg",
    }

    UNIT_CONVERSIONS = {
        "soil_moisture": {
            "from": "kg/m²",
            "to": "m³/m³",
            "factor": 0.01,  # divide by 100 (1000 kg/m³ * 0.1 m)
            "offset": 0,
        },
        "evapotranspiration": {
            "from": "W/m²",
            "to": "mm/day",
            "factor": 0.0345,  # (86400) / (2.501e6 * 1000)
            "offset": 0,
        },
        "runoff": {
            "from": "kg/m²/s",
            "to": "mm/day",
            "factor": 86400,
            "offset": 0,
        },
        "subsurface_runoff": {
            "from": "kg/m²/s",
            "to": "mm/day",
            "factor": 86400,
            "offset": 0,
        },
    }

    def __init__(self, variable: str):
        dataset_map = {
            "soil_moisture": "gldas_soil_moisture",
            "evapotranspiration": "gldas_evapotranspiration",
            "runoff": "gldas_runoff",
            "subsurface_runoff": "gldas_subsurface_runoff",
        }
        super().__init__(dataset_map.get(variable, "gldas_soil_moisture"))
        self.variable = variable
        self.gldas_var = self.VARIABLE_MAP.get(variable, "SoilMoi0_10cm_inst")
        self.base_url = "https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_M.2.1/"
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
        """Discover available GLDAS monthly granules."""
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

                # GLDAS monthly file naming
                filename = f"GLDAS_NOAH025_M.A{year}{month:02d}.021.nc4"
                url = f"{self.base_url}{year}/{filename}"

                granules.append({
                    "filename": filename,
                    "url": url,
                    "year": year,
                    "month": month,
                    "start_time": f"{year}-{month:02d}-01T00:00:00Z",
                    "end_time": f"{year}-{month:02d}-28T23:59:59Z",
                    "size_bytes": 100000000,  # ~100 MB
                })

        return granules

    async def retrieve(
        self,
        granules: List[Dict[str, Any]],
        output_dir: str
    ) -> List[str]:
        """Download GLDAS granules to local files."""
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
        """Inspect GLDAS NetCDF file metadata."""
        metadata = {"error": None}
        try:
            import xarray as xr
            ds = xr.open_dataset(file_path)
            metadata["variables"] = list(ds.data_vars)
            metadata["dimensions"] = dict(ds.dims)
            metadata["coords"] = list(ds.coords)
            metadata["attrs"] = dict(ds.attrs)

            if self.gldas_var in ds.data_vars:
                var = ds[self.gldas_var]
                metadata[f"{self.gldas_var}_shape"] = var.shape
                metadata[f"{self.gldas_var}_attrs"] = dict(var.attrs)

            ds.close()
        except Exception as e:
            metadata["error"] = str(e)

        return metadata

    def normalize(self, data: Any, variable: str) -> Any:
        """Normalize GLDAS variables to standard units."""
        if isinstance(data, dict) or isinstance(data, str):
            return data

        if variable in self.UNIT_CONVERSIONS:
            conv = self.UNIT_CONVERSIONS[variable]
            normalized = data * conv["factor"] + conv["offset"]
            normalized.attrs["units"] = conv["to"]
            normalized.attrs["original_units"] = conv["from"]
            if conv["offset"] != 0:
                normalized.attrs["conversion"] = f"multiplied by {conv['factor']} and added {conv['offset']}"
            else:
                normalized.attrs["conversion"] = f"multiplied by {conv['factor']}"
            return normalized

        return data