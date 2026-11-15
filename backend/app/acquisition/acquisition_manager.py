"""Resolve registry choices to provider-specific acquisition pipelines."""
from app.registry.dataset_registry import get_dataset
from app.acquisition.earthdata_pipeline import acquire as acquire_gpm
from app.acquisition.noaa_pipeline import acquire as acquire_noaa

async def acquire(request, investigation_id: str):
    dataset_id=request.dataset_id or "gpm_imerg_monthly"
    dataset=get_dataset(dataset_id)
    if dataset is None: raise ValueError(f"Dataset '{dataset_id}' is not supported")
    if request.provider and request.provider != dataset["provider"]: raise ValueError("Requested provider does not supply this dataset")
    pipeline_name=dataset.get("pipeline")
    if pipeline_name == "earthdata_pipeline": return await acquire_gpm(request,investigation_id)
    if pipeline_name == "noaa_pipeline": return await acquire_noaa(request,investigation_id)
    raise ValueError(f"Dataset '{dataset_id}' does not have an enabled acquisition pipeline")
