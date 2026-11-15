"""Normalized scientific time-series model; source metadata is retained."""
from dataclasses import dataclass
from typing import Any
import pandas as pd
import xarray as xr

@dataclass
class NormalizedDataset:
    data: xr.DataArray
    variable: str
    units: str
    provider: str
    dataset_id: str
    source_metadata: dict[str, Any]
    original_units: str
    crs: str = "EPSG:4326"
    quality_variables: dict[str, xr.DataArray] | None = None

    def to_dataset(self) -> xr.Dataset:
        dataset=self.data.to_dataset(name=self.variable)
        for name,array in (self.quality_variables or {}).items():
            dataset[name]=array
        dataset.attrs.update({"provider":self.provider,"dataset_id":self.dataset_id,"crs":self.crs,"original_units":self.original_units})
        return dataset

    def observations(self) -> pd.DataFrame:
        series = self.data.to_series().rename("value").reset_index()
        return series
