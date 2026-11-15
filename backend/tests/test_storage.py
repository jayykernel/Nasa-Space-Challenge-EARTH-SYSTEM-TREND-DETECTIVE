from datetime import datetime, timedelta, timezone
from app.storage import jobs
from app.storage.retention import cleanup_older_than

def test_retention_removes_old_terminal_job_and_scoped_artifacts(monkeypatch,tmp_path):
    data=tmp_path/"data"; monkeypatch.setattr(jobs,"DATA_ROOT",data); monkeypatch.setattr(jobs,"DB_PATH",tmp_path/"jobs.sqlite3")
    jobs.initialize(); job_id="0d0e168a-29d4-495d-a386-3fa7d5f14454"
    jobs.create(job_id,{"variable":"precipitation"}); jobs.update(job_id,status="completed",progress=100)
    old=(datetime.now(timezone.utc)-timedelta(days=10)).isoformat()
    with jobs._connect() as db: db.execute("UPDATE investigations SET updated_at=? WHERE id=?",(old,job_id))
    artifact=data/"processed"/"normalized"/job_id; artifact.mkdir(parents=True); (artifact/"grid.nc").write_bytes(b"fixture")
    assert cleanup_older_than(2)==1
    assert jobs.get(job_id) is None and not artifact.exists()
