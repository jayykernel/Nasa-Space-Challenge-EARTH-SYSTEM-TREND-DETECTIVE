from fastapi import APIRouter, HTTPException
from app.models.schemas import DatasetInfo, VariableInfo
from app.registry.dataset_registry import list_datasets
from app.registry.variable_registry import SUPPORTED_VARIABLES, get_variable

router=APIRouter(tags=["catalog"])

@router.get("/datasets",response_model=list[DatasetInfo])
async def datasets(): return list_datasets()

@router.get("/variables",response_model=list[VariableInfo])
async def variables(): return [get_variable(key) for key in SUPPORTED_VARIABLES]

@router.get("/variables/{variable_key}",response_model=VariableInfo)
async def variable(variable_key: str):
    if variable_key not in SUPPORTED_VARIABLES: raise HTTPException(404,detail=f"No verified acquisition pipeline is available for '{variable_key}'")
    return get_variable(variable_key)
