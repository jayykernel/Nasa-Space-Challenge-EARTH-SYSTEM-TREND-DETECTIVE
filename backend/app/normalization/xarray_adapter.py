"""Normalize NASA HDF5/NetCDF granules into a single time/lat/lon DataArray."""
from pathlib import Path
import re
from typing import Callable
import numpy as np
import pandas as pd
import xarray as xr
from app.normalization.common_model import NormalizedDataset

COORD_NAMES = {"latitude": "lat", "Latitude": "lat", "longitude": "lon", "Longitude": "lon"}

def load_gpm_files(paths: list[str], variable: str, geometry: dict | None = None,
                   on_progress: Callable[[int, int, str], None] | None = None) -> NormalizedDataset:
    if geometry:
        from shapely.geometry import shape
        minx,miny,maxx,maxy=shape(geometry).bounds
    else: minx,miny,maxx,maxy=-180,-90,180,90
    arrays, original_units, source = [], None, []
    quality_arrays: dict[str,list[xr.DataArray]]={}
    total_files = len(paths)
    for file_index, path in enumerate(paths, start=1):
        if on_progress:
            on_progress(file_index, total_files, Path(path).name)
        opened = None
        needs_month_time = False
        for group in ("Grid", None):
            try:
                opened = xr.open_dataset(path, engine="h5netcdf", group=group, decode_cf=True)
                if not opened.data_vars:
                    opened.close(); opened=None
                    continue
                break
            except Exception:
                try:
                    opened = xr.open_dataset(path, engine="h5netcdf", group=group, decode_cf=False)
                    if not opened.data_vars:
                        opened.close(); opened=None
                        continue
                    needs_month_time = True
                    break
                except Exception:
                    continue
        if opened is None:
            raise ValueError(f"Unable to read HDF5 granule: {Path(path).name}")
        if needs_month_time and "time" in opened.coords and opened.sizes.get("time") == 1:
            # IMERG Monthly stores a Julian-calendar time that xarray may not
            # decode without cftime. The granule's YYYYMM date is authoritative
            # for this monthly product and avoids a calendar conversion guess.
            opened = opened.assign_coords(time=[_time_from_filename(path)])
        ds = opened.rename({old: new for old, new in COORD_NAMES.items() if old in opened.dims or old in opened.coords})
        candidates = [variable, "precipitation", "precipitationCal"]
        name = next((key for key in candidates if key in ds.data_vars), None)
        if name is None:
            raise ValueError(f"Requested measurement '{variable}' was not found in {Path(path).name}; variables: {list(ds.data_vars)}")
        da = ds[name]
        lat = next((x for x in ("lat", "latitude") if x in da.coords), None)
        lon = next((x for x in ("lon", "longitude") if x in da.coords), None)
        if lat is None or lon is None:
            opened.close()
            raise ValueError(f"Granule {Path(path).name} lacks latitude/longitude coordinates")
        da = da.rename({x: y for x, y in ((lat,"lat"),(lon,"lon")) if x != y})
        # Clip before reading the HDF5 measurement array. GPM granules are global,
        # so loading a full 0.1 degree grid for one region wastes several GB.
        da = da.where((da.lat >= miny-0.2) & (da.lat <= maxy+0.2) & (da.lon >= minx-0.2) & (da.lon <= maxx+0.2), drop=True)
        for dim in list(da.dims):
            if dim.lower() in ("time", "time1") and dim != "time": da = da.rename({dim:"time"})
        if "time" not in da.dims:
            stamp = _time_from_filename(path)
            da = da.expand_dims(time=[stamp])
        if set(("lat","lon")).difference(da.dims):
            raise ValueError(f"Unexpected dimensions for {Path(path).name}: {da.dims}")
        extra = [d for d in da.dims if d not in ("time","lat","lon")]
        for dim in extra:
            if da.sizes[dim] != 1: raise ValueError(f"Unsupported non-singleton dimension {dim} in {Path(path).name}")
            da = da.isel({dim:0}, drop=True)
        da = da.transpose("time","lat","lon").sortby("lat").sortby("lon").load()
        for auxiliary in ("precipitationQualityIndex","randomError","gaugeRelativeWeighting","probabilityLiquidPrecipitation"):
            if auxiliary not in ds.data_vars: continue
            qa=ds[auxiliary]
            qa=qa.rename({x:y for x,y in (("latitude","lat"),("Latitude","lat"),("longitude","lon"),("Longitude","lon")) if x in qa.dims or x in qa.coords and x!=y})
            if "time" not in qa.dims and "time" in da.dims: qa=qa.expand_dims(time=da.time)
            qa=qa.where((qa.lat>=miny-.2)&(qa.lat<=maxy+.2)&(qa.lon>=minx-.2)&(qa.lon<=maxx+.2),drop=True)
            for dim in list(qa.dims):
                if dim not in ("time","lat","lon"):
                    if qa.sizes[dim]!=1: continue
                    qa=qa.isel({dim:0},drop=True)
            if set(("time","lat","lon")).issubset(qa.dims):
                quality_arrays.setdefault(auxiliary,[]).append(qa.transpose("time","lat","lon").sortby("lat").sortby("lon").load())
        global_attrs=dict(ds.attrs)
        opened.close()
        da = da.where(np.isfinite(da))
        attrs = dict(da.attrs)
        units = attrs.get("units") or attrs.get("Units")
        if not units: raise ValueError(f"Source granule {Path(path).name} does not declare measurement units")
        if original_units is not None and units != original_units:
            raise ValueError(f"Inconsistent units across granules: {original_units!r} and {units!r}")
        original_units = str(units)
        arrays.append(da)
        source.append({"file": Path(path).name, "source_attributes": attrs, "global_attributes": global_attrs})
    if not arrays: raise ValueError("No granules were available to normalize")
    combined = xr.concat(arrays, dim="time").sortby("time")
    times = pd.to_datetime(combined.time.values)
    duplicate_count=int(times.duplicated().sum())
    if duplicate_count: combined = combined.isel(time=np.flatnonzero(~times.duplicated()))
    combined.attrs.update({"units": original_units, "original_units": original_units, "provider": "earthdata", "dataset_id": "gpm_imerg_monthly", "source_variable": variable, "crs": "EPSG:4326", "duplicate_time_count":duplicate_count})
    quality={}
    for name,parts in quality_arrays.items():
        auxiliary=xr.concat(parts,dim="time").sortby("time")
        if pd.to_datetime(auxiliary.time.values).duplicated().any(): auxiliary=auxiliary.isel(time=np.flatnonzero(~pd.to_datetime(auxiliary.time.values).duplicated()))
        quality[name]=auxiliary.reindex(time=combined.time)
    return NormalizedDataset(combined, variable, original_units or "", "earthdata", "gpm_imerg_monthly", {"granules": source}, original_units or "", quality_variables=quality)

def _time_from_filename(path: str):
    match = re.search(r"(20\d{2})(\d{2})", Path(path).name)
    if not match: raise ValueError(f"No time coordinate or YYYYMM date found in {Path(path).name}")
    return pd.Timestamp(int(match.group(1)), int(match.group(2)), 1)
