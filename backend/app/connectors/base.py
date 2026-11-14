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


def get_connector(variable: str) -> BaseConnector:
    """Factory function to get the appropriate connector for a variable."""
    if variable == "precipitation":
        from app.connectors.gpm import GPMIMERGConnector
        return GPMIMERGConnector()
    elif variable in ["temperature", "specific_humidity", "relative_humidity"]:
        from app.connectors.merra2 import MERRA2Connector
        return MERRA2Connector(variable)
    elif variable in ["soil_moisture", "evapotranspiration", "runoff", "subsurface_runoff"]:
        from app.connectors.gldas import GLDASConnector
        return GLDASConnector(variable)
    else:
        raise ValueError(f"No connector available for variable: {variable}")