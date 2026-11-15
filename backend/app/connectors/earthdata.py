"""NASA Earthdata CMR discovery and Earthaccess downloads."""
from __future__ import annotations
import asyncio
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any
import earthaccess

_AUTH_ENV_LOCK=threading.RLock()

class EarthdataGPMConnector:
    short_name = "GPM_3IMERGM"
    version = "07"

    async def discover(self, time_range: dict, geometry: dict) -> list[Any]:
        def search():
            with _earthdata_environment():
                has_token=bool(os.getenv("EARTHDATA_TOKEN"))
                has_userpass=bool(os.getenv("EARTHDATA_USERNAME") and os.getenv("EARTHDATA_PASSWORD"))
                if not (has_token or has_userpass):
                    raise RuntimeError("NASA Earthdata credentials are required. Set NASA_EARTHDATA_USERNAME and NASA_EARTHDATA_PASSWORD in backend/.env.")
                login = earthaccess.login(strategy="environment", persist=False)
                if not login.authenticated:
                    raise RuntimeError("NASA Earthdata Login did not authenticate. Check the configured credentials.")
            coords = _coordinates(geometry)
            bounds = (min(x for x, _ in coords), min(y for _, y in coords), max(x for x, _ in coords), max(y for _, y in coords))
            return earthaccess.search_data(short_name=self.short_name, version=self.version, bounding_box=bounds,
                temporal=(f"{time_range['start']}T00:00:00", f"{time_range['end']}T23:59:59"))
        return await asyncio.to_thread(search)

    async def retrieve(self, granules: list[Any], directory: Path) -> list[str]:
        if not granules:
            return []
        def download():
            paths = earthaccess.download(granules, str(directory))
            return [str(Path(path).resolve()) for path in paths]
        return await asyncio.to_thread(download)

def _coordinates(geometry: dict) -> list[tuple[float,float]]:
    from shapely.geometry import shape
    geom = shape(geometry)
    return list(geom.exterior.coords) if geom.geom_type == "Polygon" else [p for poly in geom.geoms for p in poly.exterior.coords]

def granule_metadata(granule: Any) -> dict[str, Any]:
    umm=granule.get("umm",{})
    temporal=umm.get("TemporalExtent",{}).get("RangeDateTime",{})
    return {"granule_id":umm.get("GranuleUR"),
            "time_start":temporal.get("BeginningDateTime"),"time_end":temporal.get("EndingDateTime"),
            "size_mb":granule.get("size"),"links":granule.data_links(access="direct") if hasattr(granule,"data_links") else []}

@contextmanager
def _earthdata_environment():
    """Bridge app config names into earthaccess without persisting secrets."""
    with _AUTH_ENV_LOCK:
        aliases={"EARTHDATA_USERNAME":"NASA_EARTHDATA_USERNAME","EARTHDATA_PASSWORD":"NASA_EARTHDATA_PASSWORD"}
        previous={key:os.environ.get(key) for key in aliases}
        try:
            for target,source in aliases.items():
                if not os.environ.get(target) and os.environ.get(source): os.environ[target]=os.environ[source]
            yield
        finally:
            for key,value in previous.items():
                if value is None: os.environ.pop(key,None)
                else: os.environ[key]=value
