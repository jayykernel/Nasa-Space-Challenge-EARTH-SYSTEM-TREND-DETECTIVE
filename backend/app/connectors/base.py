"""Base connector interface for NASA dataset connectors."""
from abc import ABC, abstractmethod
from typing import Any
from datetime import datetime
from app.models.schemas import Geometry, TimeRange


class BaseConnector(ABC):
    """Abstract base class for NASA dataset connectors."""

    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
        self.auth_token: str | None = None

    @abstractmethod
    async def discover(
        self,
        geometry: Geometry,
        time_range: TimeRange,
        variable: str
    ) -> list[dict[str, Any]]:
        """
        Discover available granules for the given query.

        Returns:
            List of granule metadata dicts with keys like:
            - url: download/access URL
            - start_time, end_time: temporal coverage
            - bounding_box: spatial coverage
            - size_bytes: file size
        """
        pass

    @abstractmethod
    async def retrieve(
        self,
        granules: list[dict[str, Any]],
        output_dir: str
    ) -> list[str]:
        """
        Download or subset granules to local files.

        Returns:
            List of local file paths
        """
        pass

    @abstractmethod
    async def inspect_metadata(self, file_path: str) -> dict[str, Any]:
        """
        Inspect metadata of a downloaded file.

        Returns:
            Dict with variable names, dimensions, coordinates, units, etc.
        """
        pass

    @abstractmethod
    def normalize(self, data: Any, variable: str) -> Any:
        """
        Normalize data to standard units and format.

        Returns:
            xarray DataArray or Dataset with standardized coordinates and units
        """
        pass

    async def authenticate(self, username: str, password: str) -> bool:
        """Authenticate with NASA Earthdata."""
        self.auth_token = f"{username}:{password}"  # Simplified - use proper auth in production
        return True

    def get_collection_id(self) -> str:
        """Get the NASA collection ID for this connector."""
        return self.dataset_id


class GPMIMERGConnector(BaseConnector):
    """Connector for GPM IMERG Monthly Precipitation data."""

    def __init__(self):
        super().__init__("gpm_imerg_monthly")
        self.base_url = "https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGM.07/"

    async def discover(
        self,
        geometry: Geometry,
        time_range: TimeRange,
        variable: str
    ) -> list[dict[str, Any]]:
        """Discover GPM IMERG monthly granules."""
        # This is a stub implementation - real implementation would use earthaccess
        # or query the CMR API directly
        granules = []

        # Parse time range
        start_year = int(time_range.start[:4])
        end_year = int(time_range.end[:4])

        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                # Skip if outside exact range
                if year == start_year and month < int(time_range.start[5:7]):
                    continue
                if year == end_year and month > int(time_range.end[5:7]):
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
                    "end_time": f"{year}-{month:02d}-28T23:59:59Z",  # approximate
                    "size_bytes": 50_000_000,  # ~50 MB per file
                })

        return granules

    async def retrieve(
        self,
        granules: list[dict[str, Any]],
        output_dir: str
    ) -> list[str]:
        """Download GPM IMERG granules."""
        import os
        import httpx

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
                        import base64
                        auth_header = base64.b64encode(self.auth_token.encode()).decode()
                        headers["Authorization"] = f"Basic {auth_header}"

                    response = await client.get(granule["url"], headers=headers)
                    response.raise_for_status()

                    with open(local_path, "wb") as f:
                        f.write(response.content)

                    local_files.append(local_path)
                except Exception as e:
                    print(f"Failed to download {granule['url']}: {e}")
                    # Continue with other granules

        return local_files

    async def inspect_metadata(self, file_path: str) -> dict[str, Any]:
        """Inspect HDF5 file metadata."""
        import h5py

        metadata = {}
        try:
            with h5py.File(file_path, "r") as f:
                metadata["groups"] = list(f.keys())
                metadata["attributes"] = dict(f.attrs)

                # Check for precipitation variable
                if "Grid" in f:
                    grid = f["Grid"]
                    metadata["grid_variables"] = list(grid.keys())

                    if "precipitation" in grid:
                        precip = grid["precipitation"]
                        metadata["precipitation_shape"] = precip.shape
                        metadata["precipitation_attrs"] = dict(precip.attrs)

                # Get geolocation info
                if "lat" in f:
                    metadata["lat_shape"] = f["lat"].shape
                if "lon" in f:
                    metadata["lon_shape"] = f["lon"].shape

        except Exception as e:
            metadata["error"] = str(e)

        return metadata

    def normalize(self, data: Any, variable: str) -> Any:
        """Normalize GPM IMERG precipitation to mm/day."""
        import xarray as xr
        import numpy as np

        if isinstance(data, xr.DataArray):
            # GPM IMERG monthly precipitation is in mm/hr
            # Convert to mm/day
            normalized = data * 24.0
            normalized.attrs["units"] = "mm/day"
            normalized.attrs["original_units"] = "mm/hr"
            normalized.attrs["conversion"] = "multiplied by 24"
            return normalized

        return data


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

    async def discover(
        self,
        geometry: Geometry,
        time_range: TimeRange,
        variable: str
    ) -> list[dict[str, Any]]:
        """Discover MERRA-2 monthly granules."""
        granules = []

        start_year = int(time_range.start[:4])
        end_year = int(time_range.end[:4])

        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                if year == start_year and month < int(time_range.start[5:7]):
                    continue
                if year == end_year and month > int(time_range.end[5:7]):
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
                    "size_bytes": 150_000_000,  # ~150 MB per file
                })

        return granules

    async def retrieve(
        self,
        granules: list[dict[str, Any]],
        output_dir: str
    ) -> list[str]:
        """Download MERRA-2 granules."""
        import os
        import httpx

        os.makedirs(output_dir, exist_ok=True)
        local_files = []

        async with httpx.AsyncClient(timeout=600.0) as client:
            for granule in granules:
                local_path = os.path.join(output_dir, granule["filename"])

                if os.path.exists(local_path):
                    local_files.append(local_path)
                    continue

                try:
                    headers = {}
                    if self.auth_token:
                        import base64
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

    async def inspect_metadata(self, file_path: str) -> dict[str, Any]:
        """Inspect NetCDF file metadata."""
        import xarray as xr

        metadata = {}
        try:
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
        import xarray as xr

        if isinstance(data, xr.DataArray):
            conv = self.UNIT_CONVERSIONS.get(variable, {"factor": 1, "offset": 0})
            normalized = data * conv["factor"] + conv["offset"]
            normalized.attrs["units"] = conv["to"]
            normalized.attrs["original_units"] = conv["from"]
            if conv["offset"] != 0:
                normalized.attrs["conversion"] = f"multiplied by {conv['factor']} and added {conv['offset']}"
            else:
                normalized.attrs["conversion"] = f"multiplied by {conv['factor']}"
            return normalized

        return data


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

    async def discover(
        self,
        geometry: Geometry,
        time_range: TimeRange,
        variable: str
    ) -> list[dict[str, Any]]:
        """Discover GLDAS monthly granules."""
        granules = []

        start_year = int(time_range.start[:4])
        end_year = int(time_range.end[:4])

        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                if year == start_year and month < int(time_range.start[5:7]):
                    continue
                if year == end_year and month > int(time_range.end[5:7]):
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
                    "size_bytes": 100_000_000,  # ~100 MB per file
                })

        return granules

    async def retrieve(
        self,
        granules: list[dict[str, Any]],
        output_dir: str
    ) -> list[str]:
        """Download GLDAS granules."""
        import os
        import httpx

        os.makedirs(output_dir, exist_ok=True)
        local_files = []

        async with httpx.AsyncClient(timeout=600.0) as client:
            for granule in granules:
                local_path = os.path.join(output_dir, granule["filename"])

                if os.path.exists(local_path):
                    local_files.append(local_path)
                    continue

                try:
                    headers = {}
                    if self.auth_token:
                        import base64
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

    async def inspect_metadata(self, file_path: str) -> dict[str, Any]:
        """Inspect NetCDF file metadata."""
        import xarray as xr

        metadata = {}
        try:
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
        import xarray as xr

        if isinstance(data, xr.DataArray):
            conv = self.UNIT_CONVERSIONS.get(variable, {"factor": 1, "offset": 0})
            normalized = data * conv["factor"] + conv["offset"]
            normalized.attrs["units"] = conv["to"]
            normalized.attrs["original_units"] = conv["from"]
            if conv["offset"] != 0:
                normalized.attrs["conversion"] = f"multiplied by {conv['factor']} and added {conv['offset']}"
            else:
                normalized.attrs["conversion"] = f"multiplied by {conv['factor']}"
            return normalized

        return data


def get_connector(variable: str) -> BaseConnector:
    """Factory function to get the appropriate connector for a variable."""
    if variable == "precipitation":
        return GPMIMERGConnector()
    elif variable in ["temperature", "specific_humidity", "relative_humidity"]:
        return MERRA2Connector(variable)
    elif variable in ["soil_moisture", "evapotranspiration", "runoff", "subsurface_runoff"]:
        return GLDASConnector(variable)
    else:
        raise ValueError(f"No connector available for variable: {variable}")