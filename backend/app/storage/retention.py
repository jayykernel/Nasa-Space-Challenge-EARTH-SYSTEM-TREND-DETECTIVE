"""Operator-invoked retention policy for investigation artifacts."""
import argparse
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from app.storage import jobs

def cleanup_older_than(days: int) -> int:
    if days < 1: raise ValueError("Retention must be at least one day")
    cutoff=(datetime.now(timezone.utc)-timedelta(days=days)).isoformat()
    jobs.initialize(); removed=0
    with jobs._connect() as db:
        rows=db.execute("SELECT id,status,updated_at FROM investigations WHERE updated_at < ?",(cutoff,)).fetchall()
        for row in rows:
            if row["status"] not in ("completed","partial","failed","cancelled"): continue
            job_id=row["id"]
            for base in (jobs.DATA_ROOT/"raw"/"earthdata",jobs.DATA_ROOT/"raw"/"noaa",jobs.DATA_ROOT/"processed"/"normalized",jobs.DATA_ROOT/"processed"/"cleaned",jobs.DATA_ROOT/"processed"/"aggregated",jobs.DATA_ROOT/"results"/"investigations",jobs.DATA_ROOT/"metadata"/"acquisition_records"):
                target=(base/job_id).resolve()
                target.relative_to(base.resolve())
                if target.is_dir(): shutil.rmtree(target)
            db.execute("DELETE FROM investigations WHERE id=?",(job_id,)); removed+=1
        cache_rows=db.execute("SELECT granule_key,file_path FROM raw_cache WHERE last_used_at < ?",(cutoff,)).fetchall()
        cache_root=(jobs.DATA_ROOT/"raw"/"earthdata"/"cache").resolve()
        for row in cache_rows:
            target=Path(row["file_path"]).resolve()
            try:
                target.relative_to(cache_root)
            except ValueError:
                continue
            if target.is_file(): target.unlink()
            db.execute("DELETE FROM raw_cache WHERE granule_key=?",(row["granule_key"],))
    return removed

if __name__=="__main__":
    parser=argparse.ArgumentParser(description="Delete old terminal investigation records and artifacts")
    parser.add_argument("--older-than-days",type=int,default=90)
    args=parser.parse_args()
    print(cleanup_older_than(args.older_than_days))
