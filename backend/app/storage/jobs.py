"""Small SQLite-backed job repository; artifacts remain separate files."""
from __future__ import annotations
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DATA_ROOT = Path(os.getenv("EARTH_DATA_DIR", Path(__file__).resolve().parents[2] / "data"))
DB_PATH = Path(os.getenv("EARTH_JOBS_DB", DATA_ROOT / "results" / "investigations.sqlite3"))

def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def initialize():
    with _connect() as db:
        db.execute("CREATE TABLE IF NOT EXISTS investigations (id TEXT PRIMARY KEY, status TEXT NOT NULL, progress INTEGER NOT NULL, message TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, request_json TEXT NOT NULL, result_json TEXT, error TEXT)")
        db.execute("UPDATE investigations SET status='failed',progress=100,message='Backend restarted while this job was active',error='Worker interrupted by backend restart',updated_at=? WHERE status IN ('queued','retrieving_data','validating','normalizing','processing','analyzing')",(datetime.now(timezone.utc).isoformat(),))
        db.execute("CREATE TABLE IF NOT EXISTS raw_cache (granule_key TEXT PRIMARY KEY, file_path TEXT NOT NULL, checksum TEXT NOT NULL, size_bytes INTEGER NOT NULL, created_at TEXT NOT NULL, last_used_at TEXT NOT NULL)")

def create(job_id: str, request: dict[str, Any]):
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as db:
        db.execute("INSERT INTO investigations(id,status,progress,message,created_at,updated_at,request_json) VALUES(?,?,?,?,?,?,?)", (job_id,"queued",0,"Investigation queued",now,now,json.dumps(request, default=str)))

def update(job_id: str, *, status: str | None = None, progress: int | None = None, message: str | None = None, result: dict | None = None, error: str | None = None):
    fields, values = [], []
    for name, value in (("status",status),("progress",progress),("message",message),("result_json",json.dumps(result, default=str) if result is not None else None),("error",error)):
        if value is not None:
            fields.append(f"{name}=?"); values.append(value)
    fields.append("updated_at=?"); values.append(datetime.now(timezone.utc).isoformat()); values.append(job_id)
    with _connect() as db:
        db.execute(f"UPDATE investigations SET {', '.join(fields)} WHERE id=?", values)

def get(job_id: str) -> dict | None:
    with _connect() as db:
        row = db.execute("SELECT * FROM investigations WHERE id=?", (job_id,)).fetchone()
    if row is None: return None
    item = dict(row)
    item["request"] = json.loads(item.pop("request_json"))
    item["result"] = json.loads(item.pop("result_json")) if item.get("result_json") else None
    return item

def get_cached_granule(granule_key: str) -> dict | None:
    with _connect() as db:
        row=db.execute("SELECT * FROM raw_cache WHERE granule_key=?",(granule_key,)).fetchone()
        if row is None: return None
        db.execute("UPDATE raw_cache SET last_used_at=? WHERE granule_key=?",(datetime.now(timezone.utc).isoformat(),granule_key))
    return dict(row)

def cache_granule(granule_key: str, file_path: str, checksum: str, size_bytes: int):
    now=datetime.now(timezone.utc).isoformat()
    with _connect() as db:
        db.execute("INSERT INTO raw_cache(granule_key,file_path,checksum,size_bytes,created_at,last_used_at) VALUES(?,?,?,?,?,?) ON CONFLICT(granule_key) DO UPDATE SET file_path=excluded.file_path,checksum=excluded.checksum,size_bytes=excluded.size_bytes,last_used_at=excluded.last_used_at",(granule_key,file_path,checksum,size_bytes,now,now))
