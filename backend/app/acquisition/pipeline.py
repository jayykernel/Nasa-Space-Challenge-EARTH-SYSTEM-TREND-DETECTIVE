"""End-to-end investigation worker with explicit persisted stage transitions."""
from __future__ import annotations
import asyncio, json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
from app.acquisition.acquisition_manager import acquire
from app.analytics.trend import comprehensive_trend_analysis
from app.analytics.spatial_trends import spatial_trends
from app.insights.explanation import explain
from app.models.schemas import InvestigationRequest
from app.normalization.xarray_adapter import load_gpm_files
from app.normalization.noaa_adapter import load_noaa_files
from app.processing.spatial import extract_area_weighted, extract_station_mean
from app.processing.quality_control import summarize_quality
from app.processing.cleaning import clean_series
from app.processing.aggregation import aggregate
from app.processing.units import normalize_units
from app.registry.dataset_registry import get_dataset
from app.storage import jobs

async def run_investigation(investigation_id: str):
    item=jobs.get(investigation_id)
    if not item or item["status"]=="cancelled": return
    try:
        request=InvestigationRequest.model_validate(item["request"])
        jobs.update(investigation_id,status="retrieving_data",progress=8,message="Searching provider catalog for matching precipitation observations")
        acquisition, validations=await acquire(request,investigation_id)
        if jobs.get(investigation_id)["status"]=="cancelled": return
        jobs.update(investigation_id,status="validating",progress=30,message=f"Validated {len(validations)} downloaded granules")
        jobs.update(investigation_id,status="normalizing",progress=40,message="Reading source measurements and units")
        is_noaa=acquisition.provider=="noaa"
        if is_noaa:
            normalized = await asyncio.to_thread(load_noaa_files, acquisition.raw_files, request.variable)
        else:
            def normalization_progress(index: int, total: int, filename: str):
                # Persist progress occasionally so large multi-decade requests remain visibly active.
                if index == 1 or index == total or index % 3 == 0:
                    progress = 40 + int(18 * index / max(1, total))
                    jobs.update(investigation_id, status="normalizing", progress=progress,
                                message=f"Reading granule {index:,} of {total:,} · {filename}")
            normalized = await asyncio.to_thread(load_gpm_files, acquisition.raw_files, request.variable,
                                                  request.geometry, normalization_progress)
        if jobs.get(investigation_id)["status"]=="cancelled": return
        normalized.data=normalize_units(normalized.data,request.variable)
        normalized_dir=jobs.DATA_ROOT/"processed"/"normalized"/investigation_id
        normalized_dir.mkdir(parents=True,exist_ok=True)
        normalized_path=normalized_dir/"regional-grid.nc"
        await asyncio.to_thread(normalized.to_dataset().to_netcdf,normalized_path)
        jobs.update(investigation_id,status="processing",progress=60,message="Extracting area-weighted measurements for the selected region")
        regional,cells=await asyncio.to_thread(extract_station_mean if is_noaa else extract_area_weighted,normalized.data,request.geometry)
        if jobs.get(investigation_id)["status"]=="cancelled": return
        clean=clean_series(regional.time.values,regional.values)
        missing_months=_missing_months(pd.to_datetime(clean.loc[pd.notna(clean.value),"time"],utc=True),request.time_range.start,request.time_range.end)
        clean_dir=jobs.DATA_ROOT/"processed"/"cleaned"/investigation_id
        clean_dir.mkdir(parents=True,exist_ok=True)
        clean_path=clean_dir/"regional-monthly.csv"
        await asyncio.to_thread(clean.to_csv,clean_path,index=False)
        frame=aggregate(clean,request.temporal_resolution,variable=request.variable,accumulation=is_noaa)
        aggregate_dir=jobs.DATA_ROOT/"processed"/"aggregated"/investigation_id
        aggregate_dir.mkdir(parents=True,exist_ok=True)
        aggregate_path=aggregate_dir/f"{request.temporal_resolution}.csv"
        await asyncio.to_thread(frame.to_csv,aggregate_path,index=False)
        times=pd.to_datetime(frame.time,utc=True); values=frame.value.to_numpy(dtype=float)
        quality=summarize_quality(values)
        jobs.update(investigation_id,status="analyzing",progress=78,message="Calculating trend statistics and uncertainty")
        period=4 if request.temporal_resolution=="seasonal" else request.analysis.seasonal_period
        stats=comprehensive_trend_analysis(times,values,alpha=request.analysis.alpha,period=period)
        if request.temporal_resolution=="annual":
            stats["seasonal_mann_kendall"]={"trend":"not_applicable","p_value":None,"significant":None,"seasons_used":0}
        mapped=spatial_trends(cells,normalized.data.time.values)
        if jobs.get(investigation_id)["status"]=="cancelled": return
        dataset=get_dataset(acquisition.dataset_id)
        series=[]
        # Map anomalies by timestamp without substituting values for missing observations.
        from app.analytics.anomalies import monthly_anomalies
        anomalies=monthly_anomalies(times,values)
        for i,(stamp,value) in enumerate(zip(times,values)):
            series.append({"timestamp":stamp.isoformat(),"value":float(value) if pd.notna(value) else None,"anomaly":anomalies[i]})
        completed=datetime.now(timezone.utc).isoformat()
        limitations=["For flagged serial dependence, the Mann–Kendall variance uses an approximate detrended AR(1) correction; it is not a full seasonal autocorrelation model.","The Sen slope confidence interval does not account for serial correlation.","Statistical trend detection does not establish causation."]
        limitations.extend(["NOAA observations are sampled at reporting stations; the regional series is an equal-weight mean of stations inside the selected polygon, not a continuous area-weighted grid.","Station availability and reporting practices vary by place and month."] if is_noaa else ["The monthly satellite product reflects retrieval and algorithm uncertainty."])
        if missing_months: limitations.append(f"{len(missing_months)} monthly intervals had no usable observation in the requested span.")
        result={"investigation_id":investigation_id,"status":"partial" if missing_months else "completed","variable":request.variable,"variables":[request.variable],
                "dataset_metadata":[dataset],"dataset":{"id":dataset["feature_id"],"provider":dataset["provider"],"product_version":dataset["version"]},
                "region":request.geometry,"time_range":request.time_range.model_dump(mode="json"),"temporal_resolution":request.temporal_resolution,
                "time_series":{request.variable:series},"trend_statistics":{request.variable:stats},"spatial_results":{request.variable:mapped},
                "units":{request.variable:normalized.units},"data_quality":{"observation_count":quality["observation_count"],"missing_percentage":100*len(missing_months)/max(1,len(pd.period_range(pd.Timestamp(request.time_range.start).to_period("M"),pd.Timestamp(request.time_range.end).to_period("M"),freq="M"))),
                "granules_retrieved":None if is_noaa else acquisition.source_metadata.get("granule_count",len(acquisition.raw_files)),"stations_used":acquisition.source_metadata.get("station_count"),"missing_months":missing_months,"quality_fields_available":sorted(normalized.quality_variables or {}),
                "duplicate_time_count":normalized.data.attrs.get("duplicate_time_count",0),
                "files":[{"file":Path(x["path"]).name,"size_bytes":x["size_bytes"],"sha256":x["sha256"]} for x in validations]},
                "methodology":("NOAA CDO v2 GSOM monthly PRCP station observations; station values are averaged equally inside the selected geometry; monthly accumulations are summed for coarser periods; Mann–Kendall, seasonal Mann–Kendall, Sen slope and OLS against elapsed years." if is_noaa else "CMR-discovered GPM IMERG monthly V07 HDF5; source units preserved; spherical area-weighted regional mean; Mann–Kendall, seasonal Mann–Kendall, Sen slope and OLS against elapsed years."),
                "limitations":limitations,"insights":explain(request.variable,stats,normalized.units),"completed_at":completed,
                "processed_files":{"normalized_grid":str(normalized_path.relative_to(jobs.DATA_ROOT)),"cleaned_series":str(clean_path.relative_to(jobs.DATA_ROOT)),"aggregated_series":str(aggregate_path.relative_to(jobs.DATA_ROOT))},
        "provenance":{"provider":acquisition.provider,"dataset_id":acquisition.dataset_id,"product_version":acquisition.product_version,
                "raw_files":[Path(x).name for x in acquisition.raw_files],"source_metadata":acquisition.source_metadata,
                "acquisition_metadata":{"granule_count":None if is_noaa else len(acquisition.raw_files),"station_count":acquisition.source_metadata.get("station_count"),"checksums":[x["sha256"] for x in validations]}}}
        root=jobs.DATA_ROOT/"results"/"investigations"/investigation_id
        root.mkdir(parents=True,exist_ok=True)
        from app.reports.generator import generate_report
        result["report"]=generate_report(result)
        (root/"results.json").write_text(json.dumps(result,indent=2,default=str),encoding="utf-8")
        (root/"report.json").write_text(json.dumps(result["report"],indent=2,default=str),encoding="utf-8")
        metadata_dir=jobs.DATA_ROOT/"metadata"/"acquisition_records"/investigation_id
        metadata_dir.mkdir(parents=True,exist_ok=True)
        (metadata_dir/"record.json").write_text(json.dumps({"acquisition":acquisition.model_dump(mode="json"),"file_validation":validations,"result_path":str((root/"results.json").relative_to(jobs.DATA_ROOT))},indent=2,default=str),encoding="utf-8")
        final_status=result["status"]
        jobs.update(investigation_id,status=final_status,progress=100,message="Analysis complete" if final_status=="completed" else "Analysis complete with missing monthly intervals",result=result)
    except Exception as exc:
        jobs.update(investigation_id,status="failed",progress=100,message=str(exc),error=f"{type(exc).__name__}: {exc}")

def _missing_months(times,start,end):
    start=pd.Timestamp(start).to_period("M"); end=pd.Timestamp(end).to_period("M")
    if not len(times): return [str(x) for x in pd.period_range(start,end,freq="M")]
    observed=set(pd.DatetimeIndex(pd.to_datetime(times,utc=True)).tz_localize(None).to_period("M"))
    return [str(p) for p in pd.period_range(start,end,freq="M") if p not in observed]
