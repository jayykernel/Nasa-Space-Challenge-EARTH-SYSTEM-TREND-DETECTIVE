"""Geometry validation and spherical area-weighted gridded extraction."""
from __future__ import annotations
import numpy as np
import xarray as xr
from shapely.geometry import shape, Polygon, Point

def validate_geometry(geojson: dict) -> tuple[bool, str | None]:
    try:
        geom = shape(geojson)
        return (geom.is_valid and not geom.is_empty and geom.geom_type in ("Polygon","MultiPolygon"), None if geom.is_valid else "Invalid polygon")
    except Exception as exc: return False, str(exc)

def extract_area_weighted(da: xr.DataArray, geojson: dict) -> tuple[xr.DataArray, list[dict]]:
    geom = shape(geojson)
    lats, lons = np.asarray(da.lat.values), np.asarray(da.lon.values)
    minx,miny,maxx,maxy = geom.bounds
    yi=np.flatnonzero((lats>=miny-1)&(lats<=maxy+1)); xi=np.flatnonzero((lons>=minx-1)&(lons<=maxx+1))
    if not len(yi) or not len(xi): raise ValueError("Selected region does not overlap the dataset grid")
    ybounds = _bounds(lats); xbounds = _bounds(lons)
    cells=[]; weights=[]; indices=[]
    for i in yi:
        for j in xi:
            cell=Polygon([(xbounds[j],ybounds[i]),(xbounds[j+1],ybounds[i]),(xbounds[j+1],ybounds[i+1]),(xbounds[j],ybounds[i+1])])
            area=cell.intersection(geom).area
            if area>0:
                # Spherical area factor for an intersection in longitude/latitude degrees.
                weight=area*max(0.0,np.cos(np.deg2rad(lats[i])))
                if weight>0:
                    indices.append((int(i),int(j))); weights.append(weight)
                    cells.append({"lat":float(lats[i]),"lon":float(lons[j]),"lat_index":int(i),"lon_index":int(j),"intersection_area_deg2":float(area)})
    if not indices: raise ValueError("No data-grid cells intersect the selected geometry")
    values=np.stack([da.isel(lat=i,lon=j).values for i,j in indices],axis=-1)
    w=np.asarray(weights,float)
    valid=np.isfinite(values)
    weighted=np.nansum(values*w,axis=-1)/np.where((valid*w).sum(axis=-1)>0,(valid*w).sum(axis=-1),np.nan)
    regional=xr.DataArray(weighted,dims=("time",),coords={"time":da.time},name=da.name,attrs=dict(da.attrs))
    for c,(i,j) in zip(cells,indices): c["series"]=[float(v) if np.isfinite(v) else None for v in da.isel(lat=i,lon=j).values]
    return regional,cells

def extract_station_mean(da: xr.DataArray, geojson: dict) -> tuple[xr.DataArray, list[dict]]:
    """Equal-weight station means for point observations inside the polygon."""
    geom=shape(geojson)
    latitudes=np.asarray(da.lat.values,float); longitudes=np.asarray(da.lon.values,float)
    station_dim="station"
    selected=[index for index,(longitude,latitude) in enumerate(zip(longitudes,latitudes))
              if geom.covers(Point(float(longitude),float(latitude)))]
    if not selected: raise ValueError("No NOAA observation stations fall inside the selected region")
    station_values=np.asarray(da.isel({station_dim:selected}).values,float)
    valid=np.isfinite(station_values)
    regional_values=np.divide(np.nansum(station_values,axis=1),valid.sum(axis=1),out=np.full(len(station_values),np.nan),where=valid.sum(axis=1)>0)
    regional=xr.DataArray(regional_values,dims=("time",),coords={"time":da.time},name=da.name,attrs=dict(da.attrs))
    cells=[]
    station_ids=np.asarray(da.station.values)
    for index in selected:
        values=np.asarray(da.isel(station=index).values,float)
        cells.append({"lat":float(latitudes[index]),"lon":float(longitudes[index]),
                      "station_id":str(station_ids[index]),"series":[float(value) if np.isfinite(value) else None for value in values]})
    return regional,cells

def _bounds(values):
    values=np.asarray(values,float)
    if len(values)==1: step=0.1; return np.array([values[0]-step/2,values[0]+step/2])
    edges=np.empty(len(values)+1); edges[1:-1]=(values[:-1]+values[1:])/2; edges[0]=values[0]-(edges[1]-values[0]); edges[-1]=values[-1]+(values[-1]-edges[-2]); return edges
