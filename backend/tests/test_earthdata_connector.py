import asyncio
from types import SimpleNamespace
import earthaccess
from app.connectors.earthdata import EarthdataGPMConnector

def test_catalog_discovery_uses_named_product_version_time_and_geometry(monkeypatch):
    calls={}
    monkeypatch.setenv("NASA_EARTHDATA_USERNAME","test-user")
    monkeypatch.setenv("NASA_EARTHDATA_PASSWORD","test-password")
    monkeypatch.setattr(earthaccess,"login",lambda **kwargs: SimpleNamespace(authenticated=True))
    def search_data(**kwargs): calls.update(kwargs); return ["catalog-result"]
    monkeypatch.setattr(earthaccess,"search_data",search_data)
    geometry={"type":"Polygon","coordinates":[[[76,8],[79,8],[79,11],[76,11],[76,8]]]}
    result=asyncio.run(EarthdataGPMConnector().discover({"start":"2005-01-01","end":"2025-12-31"},geometry))
    assert result==["catalog-result"]
    assert calls["short_name"]=="GPM_3IMERGM" and calls["version"]=="07"
    assert calls["bounding_box"]==(76.0,8.0,79.0,11.0)
    assert calls["temporal"]==("2005-01-01T00:00:00","2025-12-31T23:59:59")
