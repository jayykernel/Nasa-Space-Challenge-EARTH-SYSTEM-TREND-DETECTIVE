from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from datetime import date
from fastapi.responses import Response
from app.acquisition.pipeline import run_investigation
from app.models.schemas import InvestigationCreatedResponse, InvestigationRequest, InvestigationResultsResponse, InvestigationStatusResponse
from app.registry.variable_registry import SUPPORTED_VARIABLES
from app.registry.dataset_registry import get_dataset
from app.reports.generator import to_csv, to_pdf
from app.storage import jobs

router=APIRouter(prefix="/analysis",tags=["analysis"])

@router.post("",status_code=202,response_model=InvestigationCreatedResponse)
async def start_analysis(request: InvestigationRequest,background_tasks: BackgroundTasks):
    variable_key=request.variable or ""
    if variable_key not in SUPPORTED_VARIABLES: raise HTTPException(422,detail=f"'{variable_key}' is not currently backed by a verified acquisition pipeline. Supported: {', '.join(SUPPORTED_VARIABLES)}")
    available_datasets=SUPPORTED_VARIABLES[variable_key]
    dataset_id=request.dataset_id or available_datasets[0]
    if dataset_id not in available_datasets: raise HTTPException(422,detail=f"Dataset '{dataset_id}' does not support '{variable_key}'")
    selected_dataset=get_dataset(dataset_id)
    if request.provider and selected_dataset and request.provider != selected_dataset["provider"]: raise HTTPException(422,detail=f"Dataset '{dataset_id}' is supplied by {selected_dataset['provider']}")
    if request.temporal_resolution == "daily": raise HTTPException(422,detail="Only monthly or coarser output is available from the currently supported precipitation datasets")
    if dataset_id == "gpm_imerg_monthly" and request.time_range.start < date(2000,6,1): raise HTTPException(422,detail="GPM IMERG Monthly V07 coverage begins in June 2000")
    if request.time_range.end > date.today(): raise HTTPException(422,detail="End date cannot be in the future")
    from uuid import uuid4
    job_id=str(uuid4()); jobs.create(job_id,request.model_dump(mode="json"))
    background_tasks.add_task(run_investigation,job_id)
    return {"investigation_id":job_id,"status":"queued","message":"Investigation accepted"}

@router.get("/{investigation_id}/status",response_model=InvestigationStatusResponse)
async def get_status(investigation_id: str):
    item=jobs.get(investigation_id)
    if not item: raise HTTPException(404,detail="Investigation not found")
    return {"investigation_id":investigation_id,"status":item["status"],"progress":item["progress"],"message":item["message"],"created_at":item["created_at"],"updated_at":item["updated_at"]}

@router.get("/{investigation_id}/results",response_model=InvestigationResultsResponse)
async def get_results(investigation_id: str):
    item=jobs.get(investigation_id)
    if not item: raise HTTPException(404,detail="Investigation not found")
    if item["status"] not in ("completed","partial") or not item["result"]:
        if item["status"]=="failed": raise HTTPException(422,detail=item["error"] or item["message"])
        raise HTTPException(409,detail=f"Results are not ready. Current status: {item['status']}")
    return item["result"]

@router.get("/{investigation_id}/map")
async def get_map(investigation_id: str):
    result=await get_results(investigation_id)
    return {"grid_cells":result["spatial_results"],"centroids":[cell for cells in result["spatial_results"].values() for cell in cells]}

@router.get("/{investigation_id}/report")
async def get_report(investigation_id: str,format: str=Query(default="json",pattern="^(json|csv|pdf)$")):
    result=await get_results(investigation_id); report=result["report"]
    if format=="json": return report
    if format=="csv": return Response(to_csv(result),media_type="text/csv",headers={"Content-Disposition":f"attachment; filename=investigation-{investigation_id}.csv"})
    try: content=to_pdf(report)
    except RuntimeError as exc: raise HTTPException(501,detail=str(exc)) from exc
    return Response(content,media_type="application/pdf",headers={"Content-Disposition":f"attachment; filename=investigation-{investigation_id}.pdf"})

@router.post("/{investigation_id}/cancel")
async def cancel(investigation_id: str):
    item=jobs.get(investigation_id)
    if not item: raise HTTPException(404,detail="Investigation not found")
    if item["status"] in ("completed","partial","failed"): raise HTTPException(409,detail=f"Cannot cancel a {item['status']} investigation")
    jobs.update(investigation_id,status="cancelled",progress=item["progress"],message="Investigation cancelled by user")
    return {"investigation_id":investigation_id,"status":"cancelled","message":"Cancelled"}
