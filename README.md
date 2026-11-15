# Earth System Trend Detective

A React/Cesium dashboard with a FastAPI science workflow for regional precipitation time series. It supports NASA GPM IMERG Final Monthly Precipitation V07 (`GPM_3IMERGM`) gridded satellite data and NOAA CDO Global Summary of the Month (`GSOM`) station precipitation. The UI lets you choose between those sources; results keep their source-specific units and methodology.

## Run locally (PowerShell)

1. Install Python dependencies from the backend folder:

   ```powershell
   cd backend
   python -m pip install -e ".[dev]"
   ```

2. Copy the repository `.env.example` to `backend/.env`. NASA GPM requires an Earthdata Login username and password. NOAA station data requires `NOAA_CDO_TOKEN`. Credentials are read by the backend and are not returned by the API.

3. Start the API in a PowerShell window:

   ```powershell
   cd backend
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
   ```

4. Install frontend dependencies and start the dashboard in another window:

   ```powershell
   cd frontend
   npm install
   npm run dev
   ```

   Open [http://localhost:3000](http://localhost:3000). Vite forwards `/api` calls to the local API. API documentation is at [http://localhost:8001/docs](http://localhost:8001/docs).

## Deploy

The frontend can be deployed as a Vite static app on Vercel from the `frontend/` directory. `frontend/vercel.json` enables direct links to saved investigations. Set the Vercel build-time environment variable `VITE_API_BASE_URL` to the deployed backend origin (for example, `https://your-api.onrender.com`, without `/api/v1`).

The `render.yaml` blueprint deploys the API on Render's free web service tier, so a payment card is not required. In Render, set `CORS_ORIGINS` to the exact Vercel site origin and enter rotated NASA Earthdata credentials privately; add `NOAA_CDO_TOKEN` if NOAA analysis is needed. Never commit secrets to this repository.

The free Render service sleeps after inactivity and has limited memory and CPU. Its filesystem is ephemeral, so downloaded NASA archives, job state and investigation results can be lost when the service restarts or redeploys. Long NASA analyses can exceed free-tier memory or execution limits. This setup is suitable for a shareable demonstration; reliable long-running analyses with durable results require a paid persistent backend and storage.

## Investigation workflow

The browser sends an application-level GeoJSON request. The API validates date range, geometry, variable and dataset before saving a job in SQLite. A background worker:

1. Uses `earthaccess` to search NASA CMR for GPM IMERG monthly V07 granules, or NOAA CDO v2 to discover nearby stations and retrieve GSOM monthly PRCP observations. Raw responses are preserved under the investigation's source-specific folder.
2. Checks HDF5 signatures, file size, readability, units, coordinates and timestamps; duplicate file checksums are removed.
3. Reads only the selected region's bounding window from each global granule, retains source attributes and source units, and builds a common `time, lat, lon` xarray dataset.
4. Computes an area-weighted regional mean for GPM grids or an equal-weight mean of NOAA stations inside the selected polygon. GPM monthly mean rates are day-weighted into annual/seasonal rates; NOAA monthly accumulation totals are summed. It will not turn monthly measurements into daily measurements.
5. Calculates Mann–Kendall, Seasonal Mann–Kendall, Sen slope and confidence bounds, linear regression, descriptive statistics and a detrended lag-1 autocorrelation diagnostic. When serial dependence is flagged, the Mann–Kendall variance gets an approximate AR(1) correction; its limitations are included in the report.
6. Stores the clipped normalized grid under `backend/data/processed/normalized/`, cleaned and aggregated CSV series under their matching processed folders, acquisition provenance under `backend/data/metadata/acquisition_records/`, and reproducible results/report JSON under `backend/data/results/investigations/`. SQLite retains job status and result JSON across restarts. A worker interrupted by a backend restart is marked failed, not complete.
7. A finished investigation can be reopened by adding `?investigation=<id>` to the app URL; the results panel has a copy-link action for sharing it within the same local deployment.

No sample values or placeholder statistics are used in production responses. A retrieval, file-validation or normalization failure marks the job failed. Missing time intervals are surfaced as partial coverage.

## Request example

```json
{
  "variable": "precipitation",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[[76, 8], [79, 8], [79, 11], [76, 11], [76, 8]]]
  },
  "time_range": { "start": "2005-01-01", "end": "2025-12-31" },
  "temporal_resolution": "monthly"
}
```

Legacy frontend requests with `variables: ["precipitation"]` remain accepted. Regions must be valid WGS84 Polygon or MultiPolygon geometries.

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/health` | Service status and supported variables |
| GET | `/api/v1/variables` | Variables with a working acquisition path |
| GET | `/api/v1/variables/{key}` | Variable metadata |
| GET | `/api/v1/datasets` | Verified dataset metadata |
| GET | `/api/v1/providers` | Implemented and unavailable provider integrations |
| POST | `/api/v1/analysis` | Validate request, create persistent investigation and queue worker |
| GET | `/api/v1/analysis/{id}/status` | Poll status, progress and failure detail |
| GET | `/api/v1/analysis/{id}/results` | Retrieve completed or partial measurements and analytics |
| GET | `/api/v1/analysis/{id}/map` | Per-grid-cell spatial trend data |
| GET | `/api/v1/analysis/{id}/report?format=json\|csv\|pdf` | Download report/observations |
| POST | `/api/v1/analysis/{id}/cancel` | Cancel an unfinished job |

## Storage and retention

Raw HDF5 granules, processed results and SQLite job state are kept under `backend/data/`. They are excluded from Git. Raw files are immutable once downloaded. Duplicate contents within an investigation are detected with SHA-256. Validated granules are also cached by NASA CMR granule identifier and reused by later investigations; each investigation keeps its own reference. There is no automatic deletion; operators can remove terminal investigations and cached granules unused for the selected retention period with:

```powershell
cd backend
python -m app.storage.retention --older-than-days 90
```

Set `EARTH_DATA_DIR` or `EARTH_JOBS_DB` to move storage. Set `CORS_ORIGINS` to the exact frontend origins in deployment.

## Providers and scientific limitations

- **NASA Earthdata / GPM IMERG:** implemented for CMR discovery and Earthdata-authenticated granule downloads. The 2005–2025 Tamil Nadu run was completed against live NASA data with 249 monthly observations. It is marked partial because no granules were returned for October–December 2025.
- **NOAA CDO:** implemented for GSOM monthly PRCP station records. Coverage depends on stations inside the selected polygon; the regional mean is not a continuous area-weighted grid. Longer windows require more requests and may take longer.
- **NASA AppEEARS, Giovanni, NASA Hydrology Time Series:** not implemented in this release; see `/api/v1/providers` for current status.

The globe supports country selection, location search, freehand polygons and rectangles. Administrative selection currently provides India ADM1 states and union territories. Its simplified GeoJSON is bundled from geoBoundaries gbOpen (CC BY 4.0, attribution in `frontend/src/assets/india-states-attribution.txt`).
- The GPM IMERG monthly granules cover the globe, so catalog granules are intersected via their spatial bounds and the pipeline clips measurements to the selected polygon locally. A full multi-decade request can download a large archive; start with a shorter period to evaluate storage and runtime.
- Current autocorrelation handling uses a transparent approximate AR(1) correction for the Mann–Kendall variance, not a full seasonal model. Sen confidence bounds are not autocorrelation corrected. Statistical association does not establish causation.

Product references: [NASA CMR GPM_3IMERGM V07 collection](https://cmr.earthdata.nasa.gov/search/site/collections/directory/GES_DISC/gov.nasa.eosdis), [NASA IMERG V07 technical documentation](https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation), and [NASA Earthaccess granule search guide](https://earthaccess.readthedocs.io/en/latest/user/explanation/search/). The V07 monthly product's recommended variable is `Grid/precipitation`; its monthly values are mean rates in mm/hr. The source variable and units are still checked on each retrieved file. The current V07B archive in NASA's catalog extends through September 2025; later dates are accepted by the API but may return partial coverage until new granules are published.

## Verification

Backend unit and API contract tests:

```powershell
cd backend
pytest -q
```

Frontend type check and production bundle:

```powershell
cd frontend
npm run build
```

The frontend repository does not currently define a separate automated test command. Provider credentials are not needed for the controlled test suite.
