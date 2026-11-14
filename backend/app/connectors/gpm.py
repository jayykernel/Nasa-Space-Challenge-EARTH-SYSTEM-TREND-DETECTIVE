"""Connector for GPM IMERG Monthly Precipitation data."""
import os
import httpx
import base64
import time
from typing import List, Dict, Any
from datetime import datetime
from app.connectors.base import BaseConnector
from app.registry.datasets import get_dataset_info
from app.processing.spatial import get_grid_cell_areas

class GPMIMERGConnector(BaseConnector):
    """Connector for GPM IMERG Monthly Precipitation data."""

    def __init__(self):
        super().__init__("gpm_imerg_monthly")
        self.base_url = "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGM.07/"
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
        """Discover available GPM IMERG monthly granules."""
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

                # GPM IMERG monthly file naming convention
                filename = f"3B-MO.MS.MRG.3IMERG.{year}{month:02d}01-S000000-E235959.V07B.HDF5"
                url = f"{self.base_url}{year}/{filename}"

                granules.append({
                    "filename": filename,
                    "url": url,
                    "year": year,
                    "month": month,
                    "start_time": f"{year}-{month:02d}-01T00:00:00Z",
                    "end_time": f"{year}-{month:02d}-28T23:59:59Z",
                    "size_bytes": 50000000,  # ~50 MB
                })

        return granules

    async def retrieve(
        self,
        granules: List[Dict[str, Any]],
        output_dir: str
    ) -> List[str]:
        """Download GPM IMERG granules to local files."""
        os.makedirs(output_dir, exist_ok=True)
        local_files = []

        async with httpx.AsyncClient(timeout=300.0) as client:
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
        """Inspect GPM IMERG file metadata."""
        metadata = {"error": None}
        try:
            import h5py
            with h5py.File(file_path, "r") as f:
                # Get global attributes
                metadata["global_attrs"] = dict(f.attrs)

                # Check for Grid group
                if "Grid" in f:
                    grid_group = f["Grid"]
                    metadata["grid_vars"] = list(grid_group.keys())

                    # Look for precipitation variable
                    if "precipitation" in grid_group:
                        precip_var = grid_group["precipitation"]
                        metadata["precipitation_shape"] = precip_var.shape
                        metadata["precipitation_attrs"] = dict(precip_var.attrs)

                # Get geolocation info
                if "lat" in f:
                    metadata["lat_shape"] = f["lat"].shape
                if "lon" in f:
                    metadata["lon_shape"] = f["lon"].shape

                metadata["file_size_bytes"] = os.path.getsize(file_path)

        except Exception as e:
            metadata["error"] = str(e)

        return metadata

    def normalize(self, data: Any, variable: str) -> Any:
        """Normalize GPM IMERG precipitation to mm/day."""
        # In real implementation, this would convert the actual data
        # For now, return a placeholder
        return data