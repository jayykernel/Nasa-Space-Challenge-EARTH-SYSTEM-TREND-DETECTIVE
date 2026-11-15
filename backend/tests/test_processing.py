import numpy as np
import pandas as pd
import pytest
import xarray as xr
import h5py
import shutil
from shapely.geometry import box, mapping
from app.models.schemas import InvestigationRequest
from app.processing.spatial import extract_area_weighted
from app.processing.aggregation import aggregate
from app.acquisition.base_pipeline import validate_received_files

def test_request_validates_geometry_and_dates():
    request=InvestigationRequest(variable="precipitation",geometry=mapping(box(76,8,79,11)),time_range={"start":"2005-01-01","end":"2025-12-31"})
    assert request.variable=="precipitation"
    with pytest.raises(ValueError):
        InvestigationRequest(variable="precipitation",geometry=mapping(box(76,8,79,11)),time_range={"start":"2025-01-01","end":"2005-01-01"})

def test_spatial_area_weighted_extraction_uses_intersecting_cells():
    data=xr.DataArray(np.array([[[1.,3.],[5.,7.]]]),dims=("time","lat","lon"),coords={"time":[pd.Timestamp("2020-01-01")],"lat":[0.,1.],"lon":[0.,1.]},attrs={"units":"mm h-1"})
    regional,cells=extract_area_weighted(data,mapping(box(-.49,-.49,.49,.49)))
    assert len(cells)==1
    assert np.isclose(regional.item(),1.)

def test_annual_precipitation_uses_month_day_weights():
    times=pd.date_range("2020-01-01",periods=12,freq="MS")
    frame=pd.DataFrame({"time":times,"value":np.ones(12)})
    out=aggregate(frame,"annual",variable="precipitation")
    assert len(out)==1 and out.iloc[0].value==1

def test_receiver_rejects_html_or_truncated_provider_response(tmp_path):
    bad=tmp_path/"bad.h5"; bad.write_bytes(b"<html>not data</html>")
    with pytest.raises(ValueError): validate_received_files([str(bad)])

def test_receiver_deduplicates_matching_checksums(tmp_path):
    first=tmp_path/"first.h5"; second=tmp_path/"second.h5"
    with h5py.File(first,"w") as handle:
        handle.create_dataset("observations",data=np.arange(2048))
    shutil.copyfile(first,second)
    assert len(validate_received_files([str(first),str(second)]))==1
