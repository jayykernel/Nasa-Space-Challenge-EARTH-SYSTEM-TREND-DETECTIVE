---
name: project-structure
description: Initial repository structure setup
metadata:
  type: project
---

Created repository monorepo structure at C:/dev/Nasa-Space-Challenge-EARTH-SYSTEM-TREND-DETECTIVE with:

Frontend:
- package.json with dependencies (react, typescript, vite, tailwind, leaflet, resium, cesium, zustand, @turf/turf)
- Directory structure: src/components/{globe,maps,dashboard,investigation}, src/services, src/store, src/types, src/utils

Backend:
- pyproject.toml with dependencies (fastapi, pydantic, earthaccess, xarray, numpy, pandas, scipy, rasterio, shapely, pymannkendall, geopandas)
- Directory structure: app/{main,connectors,registry,processing,analytics,models,api}
- Key modules created: app/main.py (FastAPI app with analysis endpoints), app/connectors/base.py (connector interface), app/connectors/gpm.py, app/connectors/merra2.py, app/connectors/gldas.py, app/registry/datasets.py (dataset registry with GPM, MERRA-2, GLDAS variables and datasets), app/processing/spatial.py (spatial extraction with shapely/xarray), app/processing/analytics.py (statistical analysis: linear regression, Mann-Kendall, Sen's slope), app/models/schemas.py (Pydantic models)

Infrastructure:
- .env.example with NASA Earthdata credentials template
- .claude/launch.json with Vite dev/build configurations

Tests: tests/ directory initialized

Ongoing work needed:
- Implement actual NASA data retrieval (currently stubbed)
- Build frontend UI components
- Integrate CesiumJS and LeafletJS
- Implement end-to-end investigation pipeline
- Add report generation