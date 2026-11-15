import asyncio
import hashlib
import numpy as np
import pandas as pd
import xarray as xr
from fastapi.testclient import TestClient
from shapely.geometry import box, mapping
from app.models.schemas import AcquisitionResult, InvestigationRequest
from app.acquisition import pipeline
from app.storage import jobs
from app.main import app

def test_fixture_runs_receiving_normalization_processing_analytics_and_report(monkeypatch,tmp_path):
    monkeypatch.setattr(jobs,"DB_PATH",tmp_path/"jobs.sqlite3")
    monkeypatch.setattr(jobs,"DATA_ROOT",tmp_path/"data")
    jobs.initialize()
    times=pd.date_range("2000-06-01",periods=36,freq="MS")
    trend=np.arange(36,dtype=float)[:,None,None]*0.15
    values=np.broadcast_to(2+trend,(36,2,2)).copy()
    ds=xr.Dataset({"precipitation":(("time","lat","lon"),values,{"units":"mm h-1","long_name":"precipitation rate"}),
                   "precipitationQualityIndex":(("time","lat","lon"),np.ones_like(values),{"units":"1"}),
                   "randomError":(("time","lat","lon"),np.full_like(values,.1),{"units":"mm h-1"})},
                  coords={"time":times,"lat":[9.,10.],"lon":[76.,77.]},attrs={"source":"controlled test fixture"})
    raw=tmp_path/"GPM_200006_test.h5"
    ds.to_netcdf(raw,engine="h5netcdf",group="Grid",mode="w")
    raw_bytes=raw.read_bytes()
    assert raw_bytes[:8]==b"\x89HDF\r\n\x1a\n"
    request=InvestigationRequest(variable="precipitation",geometry=mapping(box(75.8,8.8,76.4,9.4)),
        time_range={"start":"2000-06-01","end":"2003-05-31"},temporal_resolution="monthly")
    job_id="fixture-investigation"
    jobs.create(job_id,request.model_dump(mode="json"))
    async def fake_acquire(_request,_job_id):
        acquired=AcquisitionResult(investigation_id=job_id,provider="earthdata",dataset_id="gpm_imerg_monthly",product_version="07",status="completed",raw_files=[str(raw)],raw_format="HDF5",requested_variable="precipitation",requested_time_range=request.time_range,requested_geometry=request.geometry,source_metadata={"fixture":True},acquisition_metadata={"fixture":True})
        return acquired,[{"path":str(raw),"size_bytes":len(raw_bytes),"sha256":hashlib.sha256(raw_bytes).hexdigest()}]
    monkeypatch.setattr(pipeline,"acquire",fake_acquire)
    asyncio.run(pipeline.run_investigation(job_id))
    saved=jobs.get(job_id)
    assert saved["status"]=="completed",saved["error"]
    result=saved["result"]
    assert result["data_quality"]["observation_count"]==36
    assert result["data_quality"]["quality_fields_available"]==["precipitationQualityIndex","randomError"]
    assert result["units"]["precipitation"]=="mm h-1"
    assert result["trend_statistics"]["precipitation"]["sens_slope"]["slope"]>0
    assert len(result["time_series"]["precipitation"])==36
    assert result["report"]["investigation_id"]==job_id
    assert (tmp_path/"data"/"results"/"investigations"/job_id/"report.json").is_file()
    normalized_path=tmp_path/"data"/"processed"/"normalized"/job_id/"regional-grid.nc"
    normalized=xr.open_dataset(normalized_path)
    assert "precipitationQualityIndex" in normalized and "randomError" in normalized
    normalized.close()
    with TestClient(app) as client:
        response=client.get(f"/api/v1/analysis/{job_id}/results")
        assert response.status_code==200,response.text
        assert response.json()["processed_files"]["normalized_grid"]
        assert client.get(f"/api/v1/analysis/{job_id}/map").status_code==200
        csv_response=client.get(f"/api/v1/analysis/{job_id}/report?format=csv")
        assert csv_response.status_code==200 and "value,units" in csv_response.text
        pdf_response=client.get(f"/api/v1/analysis/{job_id}/report?format=pdf")
        assert pdf_response.status_code==200 and pdf_response.content.startswith(b"%PDF")
