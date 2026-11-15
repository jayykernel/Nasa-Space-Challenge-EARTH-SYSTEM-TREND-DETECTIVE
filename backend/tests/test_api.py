from fastapi.testclient import TestClient
from app.main import app
from app.api import analysis
from app.storage import jobs

def test_api_catalog_validation_job_persistence_and_failure(monkeypatch,tmp_path):
    monkeypatch.setattr(jobs,"DB_PATH",tmp_path/"jobs.sqlite3")
    async def queued_worker(_job_id): return None
    monkeypatch.setattr(analysis,"run_investigation",queued_worker)
    geometry={"type":"Polygon","coordinates":[[[76,8],[79,8],[79,11],[76,11],[76,8]]]}
    body={"variable":"precipitation","geometry":geometry,"time_range":{"start":"2005-01-01","end":"2025-12-31"},"temporal_resolution":"monthly"}
    with TestClient(app) as client:
        assert client.get("/api/v1/health").json()["status"]=="ok"
        catalog=client.get("/api/v1/datasets").json()
        assert len(catalog)==2 and "GPM_3IMERGM" in [item["dataset_short_name"] for item in catalog]
        providers=client.get("/api/v1/providers").json()
        assert next(item for item in providers if item["id"]=="noaa")["status"]=="implemented"
        invalid={**body,"temporal_resolution":"daily"}
        assert client.post("/api/v1/analysis",json=invalid).status_code==422
        created=client.post("/api/v1/analysis",json=body)
        assert created.status_code==202
        job_id=created.json()["investigation_id"]
        assert client.get(f"/api/v1/analysis/{job_id}/status").json()["status"]=="queued"
        noaa_body={**body,"dataset_id":"noaa_ghcn_monthly_precipitation","provider":"noaa","time_range":{"start":"2010-01-01","end":"2010-12-31"}}
        noaa_created=client.post("/api/v1/analysis",json=noaa_body)
        assert noaa_created.status_code==202,noaa_created.text
        noaa_id=noaa_created.json()["investigation_id"]
    # A new repository read sees the same record after the request client closes.
    assert jobs.get(job_id)["request"]["variable"]=="precipitation"
    assert jobs.get(noaa_id)["request"]["dataset_id"]=="noaa_ghcn_monthly_precipitation"
