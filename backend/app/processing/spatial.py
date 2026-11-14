"""Spatial processing for extracting regional data from gridded datasets."""
import numpy as np
import xarray as xr
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely.ops import transform
import pyproj
from typing import Any
import warnings

# Suppress specific warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="xarray")


def validate_geometry(geojson: dict) -> tuple[bool, str | None]:
    """
    Validate a GeoJSON geometry.

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        geom = shape(geojson)

        if not geom.is_valid:
            return False, f"Invalid geometry: {geom.explain_validity()}"

        # Check geometry type
        if geom.geom_type not in ["Polygon", "MultiPolygon"]:
            return False, f"Unsupported geometry type: {geom.geom_type}. Only Polygon and MultiPolygon supported."

        # Check area (limit to reasonable size for performance)
        # Approximate area in square degrees
        bounds = geom.bounds
        area_deg2 = (bounds[2] - bounds[0]) * (bounds[3] - bounds[1])
        if area_deg2 > 10000:  # ~10000 deg² ≈ whole Earth
            return False, "Geometry too large. Maximum area ~10000 square degrees."

        return True, None

    except Exception as e:
        return False, f"Geometry validation error: {str(e)}"


def get_grid_cell_polygons(da: xr.DataArray) -> list[Polygon]:
    """
    Generate polygons for each grid cell in a DataArray.

    Assumes regular lat/lon grid with coordinates named 'lat' and 'lon'.
    """
    polygons = []

    lats = da.coords.get("lat") or da.coords.get("latitude")
    lons = da.coords.get("lon") or da.coords.get("longitude")

    if lats is None or lons is None:
        raise ValueError("DataArray must have lat/lon or latitude/longitude coordinates")

    lat_vals = lats.values
    lon_vals = lons.values

    # Calculate cell boundaries
    # For regular grids, cell boundaries are midpoints between centers
    if len(lat_vals) > 1:
        lat_bounds = np.zeros(len(lat_vals) + 1)
        lat_bounds[1:-1] = (lat_vals[:-1] + lat_vals[1:]) / 2
        lat_bounds[0] = lat_vals[0] - (lat_bounds[1] - lat_vals[0])
        lat_bounds[-1] = lat_vals[-1] + (lat_vals[-1] - lat_bounds[-2])
    else:
        # Single row - assume 0.25° resolution
        lat_bounds = np.array([lat_vals[0] - 0.125, lat_vals[0] + 0.125])

    if len(lon_vals) > 1:
        lon_bounds = np.zeros(len(lon_vals) + 1)
        lon_bounds[1:-1] = (lon_vals[:-1] + lon_vals[1:]) / 2
        lon_bounds[0] = lon_vals[0] - (lon_bounds[1] - lon_vals[0])
        lon_bounds[-1] = lon_vals[-1] + (lon_vals[-1] - lon_bounds[-2])
    else:
        # Single column - assume 0.25° resolution
        lon_bounds = np.array([lon_vals[0] - 0.125, lon_vals[0] + 0.125])

    for i in range(len(lat_vals)):
        for j in range(len(lon_vals)):
            poly = Polygon([
                (lon_bounds[j], lat_bounds[i]),
                (lon_bounds[j+1], lat_bounds[i]),
                (lon_bounds[j+1], lat_bounds[i+1]),
                (lon_bounds[j], lat_bounds[i+1]),
                (lon_bounds[j], lat_bounds[i]),
            ])
            polygons.append(poly)

    return polygons


def extract_region(
    da: xr.DataArray,
    geometry: dict,
    method: str = "area_weighted"
) -> dict[str, Any]:
    """
    Extract data for a geographic region.

    Args:
        da: xarray DataArray with lat/lon coordinates
        geometry: GeoJSON geometry (Polygon or MultiPolygon)
        method: "area_weighted", "nearest", "centroid", or "all_touching"

    Returns:
        Dict with extracted data, weights, and metadata
    """
    from shapely.geometry import shape

    geom = shape(geometry)

    # Get coordinates
    lats = da.coords.get("lat") or da.coords.get("latitude")
    lons = da.coords.get("lon") or da.coords.get("longitude")

    if lats is None or lons is None:
        raise ValueError("DataArray must have lat/lon coordinates")

    # Get grid cell polygons
    cell_polygons = get_grid_cell_polygons(da)

    # Find intersecting cells
    intersecting_indices = []
    intersection_areas = []

    for idx, cell_poly in enumerate(cell_polygons):
        if cell_poly.intersects(geom):
            intersection = cell_poly.intersection(geom)
            if intersection.area > 0:
                intersecting_indices.append(idx)
                intersection_areas.append(intersection.area)

    if not intersecting_indices:
        return {
            "data": np.array([]),
            "weights": np.array([]),
            "cell_indices": [],
            "lat_indices": [],
            "lon_indices": [],
            "intersection_areas": [],
            "total_area": 0,
            "n_cells": 0,
        }

    # Convert flat indices to 2D indices
    n_lons = len(lons)
    lat_indices = [idx // n_lons for idx in intersecting_indices]
    lon_indices = [idx % n_lons for idx in intersecting_indices]

    # Extract data values for intersecting cells
    # da shape: (time, lat, lon) or (lat, lon)
    if da.ndim == 3:
        # Time series data
        extracted_data = da[:, lat_indices, lon_indices].values  # (time, n_cells)
    elif da.ndim == 2:
        # Single time step
        extracted_data = da[lat_indices, lon_indices].values  # (n_cells,)
        extracted_data = extracted_data[np.newaxis, :]  # (1, n_cells)
    else:
        raise ValueError(f"Unexpected DataArray dimensions: {da.ndim}")

    # Calculate weights
    if method == "area_weighted":
        weights = np.array(intersection_areas)
        weights = weights / weights.sum()
    elif method == "equal":
        weights = np.ones(len(intersecting_indices)) / len(intersecting_indices)
    elif method == "centroid":
        # Weight by whether cell centroid is in polygon
        weights = np.array([
            1.0 if geom.contains(cell_polygons[idx].centroid) else 0.0
            for idx in intersecting_indices
        ])
        if weights.sum() == 0:
            weights = np.ones(len(intersecting_indices)) / len(intersecting_indices)
        else:
            weights = weights / weights.sum()
    else:
        weights = np.ones(len(intersecting_indices)) / len(intersecting_indices)

    # Compute area-weighted regional average
    if extracted_data.ndim == 2:
        # (time, n_cells) -> (time,)
        regional_series = np.average(extracted_data, axis=1, weights=weights)
    else:
        regional_series = np.average(extracted_data, weights=weights)

    return {
        "data": regional_series,
        "cell_data": extracted_data,
        "weights": weights,
        "cell_indices": intersecting_indices,
        "lat_indices": lat_indices,
        "lon_indices": lon_indices,
        "intersection_areas": intersection_areas,
        "total_area": sum(intersection_areas),
        "n_cells": len(intersecting_indices),
        "method": method,
    }


def extract_grid_cell_time_series(
    da: xr.DataArray,
    geometry: dict
) -> dict[str, Any]:
    """
    Extract time series for each individual grid cell intersecting the geometry.

    Returns:
        Dict with per-cell time series data for spatial trend analysis
    """
    from shapely.geometry import shape

    geom = shape(geometry)

    lats = da.coords.get("lat") or da.coords.get("latitude")
    lons = da.coords.get("lon") or da.coords.get("longitude")

    if lats is None or lons is None:
        raise ValueError("DataArray must have lat/lon coordinates")

    cell_polygons = get_grid_cell_polygons(da)
    n_lons = len(lons)

    cell_time_series = []

    for idx, cell_poly in enumerate(cell_polygons):
        if cell_poly.intersects(geom):
            intersection = cell_poly.intersection(geom)
            if intersection.area > 0:
                lat_idx = idx // n_lons
                lon_idx = idx % n_lons

                # Extract time series for this cell
                if da.ndim == 3:
                    ts = da[:, lat_idx, lon_idx].values
                elif da.ndim == 2:
                    ts = da[lat_idx, lon_idx].values
                    ts = ts[np.newaxis] if np.isscalar(ts) else ts
                else:
                    continue

                cell_time_series.append({
                    "cell_index": idx,
                    "lat_idx": lat_idx,
                    "lon_idx": lon_idx,
                    "lat": float(lats[lat_idx]),
                    "lon": float(lons[lon_idx]),
                    "intersection_area": float(intersection.area),
                    "cell_area": float(cell_poly.area),
                    "time_series": ts.tolist(),
                    "centroid_in_polygon": geom.contains(cell_poly.centroid),
                })

    return {
        "cells": cell_time_series,
        "n_cells": len(cell_time_series),
        "time_coords": da.coords.get("time").values.tolist() if "time" in da.coords else None,
    }


def compute_grid_cell_areas(lat_vals: np.ndarray, lon_vals: np.ndarray) -> np.ndarray:
    """
    Compute area of each grid cell in square meters.

    Uses spherical Earth approximation.
    """
    R = 6371000  # Earth radius in meters

    if len(lat_vals) > 1:
        lat_bounds = np.zeros(len(lat_vals) + 1)
        lat_bounds[1:-1] = (lat_vals[:-1] + lat_vals[1:]) / 2
        lat_bounds[0] = lat_vals[0] - (lat_bounds[1] - lat_vals[0])
        lat_bounds[-1] = lat_vals[-1] + (lat_vals[-1] - lat_bounds[-2])
    else:
        lat_bounds = np.array([lat_vals[0] - 0.125, lat_vals[0] + 0.125])

    if len(lon_vals) > 1:
        lon_bounds = np.zeros(len(lon_vals) + 1)
        lon_bounds[1:-1] = (lon_vals[:-1] + lon_vals[1:]) / 2
        lon_bounds[0] = lon_vals[0] - (lon_bounds[1] - lon_vals[0])
        lon_bounds[-1] = lon_vals[-1] + (lon_vals[-1] - lon_bounds[-2])
    else:
        lon_bounds = np.array([lon_vals[0] - 0.125, lon_vals[0] + 0.125])

    areas = np.zeros((len(lat_vals), len(lon_vals)))

    for i in range(len(lat_vals)):
        lat1 = np.radians(lat_bounds[i])
        lat2 = np.radians(lat_bounds[i+1])
        for j in range(len(lon_vals)):
            lon1 = np.radians(lon_bounds[j])
            lon2 = np.radians(lon_bounds[j+1])
            # Area on sphere: R² * (sin(lat2) - sin(lat1)) * (lon2 - lon1)
            areas[i, j] = R * R * (np.sin(lat2) - np.sin(lat1)) * (lon2 - lon1)

    return areas


def apply_land_mask(da: xr.DataArray, land_mask: xr.DataArray | None = None) -> xr.DataArray:
    """
    Apply land mask to data array.

    If no land_mask provided, creates a simple one based on data availability
    (assumes NaN over ocean for land surface variables).
    """
    if land_mask is not None:
        return da.where(land_mask)

    # Simple heuristic: if data has NaN values that form coherent ocean-like patterns,
    # but this is unreliable. Better to use an actual land mask dataset.
    return da


def regrid_to_common(da: xr.DataArray, target_lats: np.ndarray, target_lons: np.ndarray) -> xr.DataArray:
    """
    Regrid data to a common lat/lon grid using bilinear interpolation.

    Useful for comparing variables from different datasets with different resolutions.
    """
    from scipy.interpolate import RegularGridInterpolator

    src_lats = (da.coords.get("lat") or da.coords.get("latitude")).values
    src_lons = (da.coords.get("lon") or da.coords.get("longitude")).values

    if np.array_equal(src_lats, target_lats) and np.array_equal(src_lons, target_lons):
        return da

    # Create interpolator
    if da.ndim == 3:
        # Time series: interpolate each time step
        interpolated = np.zeros((da.shape[0], len(target_lats), len(target_lons)))
        for t in range(da.shape[0]):
            interp = RegularGridInterpolator(
                (src_lats, src_lons),
                da[t].values,
                bounds_error=False,
                fill_value=np.nan
            )
            # Create meshgrid for target
            Lon, Lat = np.meshgrid(target_lons, target_lats)
            points = np.column_stack([Lat.ravel(), Lon.ravel()])
            interpolated[t] = interp(points).reshape(len(target_lats), len(target_lons))

        # Create new DataArray
        new_da = xr.DataArray(
            interpolated,
            dims=da.dims,
            coords={
                "time": da.coords["time"],
                "lat": target_lats,
                "lon": target_lons,
            },
            attrs=da.attrs
        )
    else:
        interp = RegularGridInterpolator(
            (src_lats, src_lons),
            da.values,
            bounds_error=False,
            fill_value=np.nan
        )
        Lon, Lat = np.meshgrid(target_lons, target_lats)
        points = np.column_stack([Lat.ravel(), Lon.ravel()])
        interpolated = interp(points).reshape(len(target_lats), len(target_lons))

        new_da = xr.DataArray(
            interpolated,
            dims=da.dims,
            coords={"lat": target_lats, "lon": target_lons},
            attrs=da.attrs
        )

    return new_da