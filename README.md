# Earth System Trend Detective

> **NASA Space Apps Challenge 2026** — *Explore Earth. Detect Change. Understand Our Planet.*

An interactive scientific investigation platform for discovering, retrieving, analyzing, and understanding environmental trends using real NASA Earth science data.

## 🎯 Mission

Build a production-quality web application that allows users to:
1. **Select** an environmental variable (rainfall, temperature, soil moisture, etc.)
2. **Select** a geographical region using an interactive 3D Earth
3. **Select** a historical time range
4. **Retrieve** corresponding NASA Earth observation or model data
5. **Extract** measurements for the selected region
6. **Perform** scientific statistical analysis
7. **Visualize** geographical and temporal distributions
8. **Generate** reproducible scientific investigation reports

## 🏗️ Architecture

```
earth-system-trend-detective/
├── frontend/                 # React + TypeScript + Vite
│   ├── src/
│   │   ├── components/
│   │   │   ├── globe/       # CesiumJS 3D Earth
│   │   │   ├── maps/        # LeafletJS 2D scientific maps
│   │   │   ├── dashboard/   # Results & visualizations
│   │   │   ├── investigation/ # Sidebar controls
│   │   │   ├── layout/      # Header, UI components
│   │   │   └── ui/          # Loading, error, shared UI
│   │   ├── services/        # API client
│   │   ├── store/           # Zustand state management
│   │   ├── types/           # TypeScript types
│   │   └── hooks/           # Custom React hooks
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── backend/                  # Python + FastAPI
│   ├── app/
│   │   ├── api/             # REST endpoints
│   │   ├── connectors/      # NASA data connectors
│   │   │   ├── base.py      # Abstract base connector
│   │   │   ├── gpm.py       # GPM IMERG precipitation
│   │   │   ├── merra2.py    # MERRA-2 atmospheric
│   │   │   └── gldas.py     # GLDAS land surface
│   │   ├── registry/        # Dataset registry
│   │   ├── processing/      # Data processing
│   │   │   ├── spatial.py   # Spatial extraction
│   │   │   └── analytics.py # Statistical analysis
│   │   ├── models/          # Pydantic schemas
│   │   └── main.py          # FastAPI app
│   └── pyproject.toml
├── tests/                    # Unit, integration, scientific tests
├── docs/                     # Documentation
├── .env.example             # Environment template
└── README.md
```

## 🛰️ NASA Data Integrations

| Variable | Dataset | Mission | Coverage | Resolution |
|----------|---------|---------|----------|------------|
| **Precipitation** | GPM IMERG Final Run V07 Monthly | GPM | 2000-06 → present | 0.1° (~11 km) |
| **Air Temperature** | MERRA-2 M2TMNXSLV | MERRA-2 | 1980-01 → present | 0.5° × 0.625° |
| **Specific Humidity** | MERRA-2 M2TMNXSLV | MERRA-2 | 1980-01 → present | 0.5° × 0.625° |
| **Relative Humidity** | MERRA-2 M2TMNXSLV | MERRA-2 | 1980-01 → present | 0.5° × 0.625° |
| **Soil Moisture** | GLDAS Noah V2.1 | GLDAS | 2000-01 → present | 0.25° (~25 km) |
| **Evapotranspiration** | GLDAS Noah V2.1 | GLDAS | 2000-01 → present | 0.25° |
| **Surface Runoff** | GLDAS Noah V2.1 | GLDAS | 2000-01 → present | 0.25° |
| **Subsurface Runoff** | GLDAS Noah V2.1 | GLDAS | 2000-01 → present | 0.25° |

*Planned: GRACE/GRACE-FO (Terrestrial Water Storage), MODIS (NDVI/EVI)*

## 📊 Statistical Analysis

- **Linear Regression**: Rate of change, R², uncertainty
- **Mann-Kendall Test**: Monotonic trend detection, p-values
- **Seasonal Mann-Kendall**: Accounts for seasonal cycles
- **Sen's Slope**: Robust trend magnitude with confidence intervals
- **Descriptive Statistics**: Mean, median, std, percentiles, missing data %
- **Autocorrelation**: Ljung-Box test for temporal dependence
- **Seasonal Decomposition**: Trend, seasonal, residual components

## 🚀 Quick Start

### Prerequisites
- Node.js 18+
- Python 3.10+
- NASA Earthdata account (for data access)

### Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### Backend
```bash
cd backend
pip install -e .  # or poetry install
cp .env.example .env
# Edit .env with your NASA Earthdata credentials
uvicorn app.main:app --reload --port 8000
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

## 🔐 NASA Earthdata Authentication

1. Create account at [https://urs.earthdata.nasa.gov/](https://urs.earthdata.nasa.gov/)
2. Authorize applications: GPM, MERRA-2, GLDAS data access
3. Set credentials in `.env`:
```bash
NASA_EARTHDATA_USERNAME=your_username
NASA_EARTHDATA_PASSWORD=your_password
```

## 🛠️ Development Phases

- [x] **Phase 0**: Repository inspection & structure
- [x] **Phase 1**: Data access proof (GPM IMERG)
- [x] **Phase 2**: Scientific processing pipeline
- [x] **Phase 3**: Backend API & investigation engine
- [x] **Phase 4**: Frontend foundation & dark theme
- [x] **Phase 5**: CesiumJS 3D Earth integration
- [x] **Phase 6**: LeafletJS scientific maps
- [ ] **Phase 7**: End-to-end integration
- [ ] **Phase 8**: Additional datasets (MERRA-2, GLDAS)
- [ ] **Phase 9**: Final validation & testing
- [ ] **Phase 10**: Demo preparation & submission

## 🎨 Design System

**Dark HYPHEN-inspired theme:**
- Background: `#0a0e17` (navy/black)
- Cards: `#161b22` (dark card)
- Borders: `#2a323c` (subtle borders)
- Primary: `#00d4ff` (cyan)
- Secondary: `#1e90ff` (blue)
- Success: `#00b894` (teal)
- Warning: `#f39c12` (yellow)
- Danger: `#e74c3c` (red)
- Text: `#e6edf3` (light)
- Muted: `#8b949e` (dim)

## 📝 Scientific Integrity

This application follows strict scientific standards:
- ✅ Never fabricates NASA measurements
- ✅ Never presents synthetic values as real results
- ✅ Clearly distinguishes evidence, statistics, interpretation
- ✅ Never claims causation from correlation
- ✅ Communicates uncertainty and limitations
- ✅ Provides full data provenance and citations

## 📚 Documentation

- [Architecture](docs/architecture.md)
- [Datasets](docs/datasets.md)
- [Data Access](docs/data_access.md)
- [Methodology](docs/methodology.md)
- [API Reference](docs/api.md)
- [Demo Script](docs/demo_script.md)

## 🤝 Contributing

This is a NASA Space Apps Challenge 2026 submission. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License — Built for NASA Space Apps Challenge 2026.

---

**Built with ❤️ for Earth science**

*Earth System Trend Detective — Explore Earth. Detect Change. Understand Our Planet.*