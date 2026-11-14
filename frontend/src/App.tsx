import { useEffect, useState } from 'react';
import { useStore } from './store/useStore';
import { InvestigationSidebar } from './components/investigation/InvestigationSidebar';
import { GlobeView } from './components/globe/GlobeView';
import { MapView } from './components/maps/MapView';
import { ResultsPanel } from './components/dashboard/ResultsPanel';
import { Header } from './components/layout/Header';
import { LoadingOverlay } from './components/ui/LoadingOverlay';
import { ErrorToast } from './components/ui/ErrorToast';
import type { VariableInfo } from './types';

const FALLBACK_VARIABLES: VariableInfo[] = [
  { key: 'precipitation', display_name: 'Rainfall / Precipitation', description: 'Precipitation rate from satellite observations.', unit: 'mm/day', data_source: 'GPM IMERG', available_coverage: '2000-06 to present', spatial_resolution: '0.1°', scientific_explanation: 'Satellite estimate of rain and other precipitation.' },
  { key: 'temperature', display_name: 'Air Temperature', description: 'Near-surface air temperature at 2 meters.', unit: '°C', data_source: 'MERRA-2', available_coverage: '1980-01 to present', spatial_resolution: '0.5° × 0.625°', scientific_explanation: 'Long-term atmospheric reanalysis of near-surface temperature.' },
  { key: 'specific_humidity', display_name: 'Specific Humidity', description: 'Mass of water vapor per mass of moist air.', unit: 'kg/kg', data_source: 'MERRA-2', available_coverage: '1980-01 to present', spatial_resolution: '0.5° × 0.625°', scientific_explanation: 'Measure of atmospheric moisture content.' },
  { key: 'relative_humidity', display_name: 'Relative Humidity', description: 'Ratio of actual to saturation water vapor pressure.', unit: '%', data_source: 'MERRA-2', available_coverage: '1980-01 to present', spatial_resolution: '0.5° × 0.625°', scientific_explanation: 'Measure of how close air is to saturation.' },
  { key: 'soil_moisture', display_name: 'Soil Moisture', description: 'Volumetric water content in the upper soil layer.', unit: 'm³/m³', data_source: 'GLDAS Noah', available_coverage: '2000-01 to present', spatial_resolution: '0.25°', scientific_explanation: 'Model estimate of water stored in surface soils.' },
  { key: 'evapotranspiration', display_name: 'Evapotranspiration', description: 'Water flux from the land surface to the atmosphere.', unit: 'mm/day', data_source: 'GLDAS Noah', available_coverage: '2000-01 to present', spatial_resolution: '0.25°', scientific_explanation: 'Combined evaporation from soil and transpiration from plants.' },
  { key: 'runoff', display_name: 'Surface Runoff', description: 'Water flowing over the land surface.', unit: 'mm/day', data_source: 'GLDAS Noah', available_coverage: '2000-01 to present', spatial_resolution: '0.25°', scientific_explanation: 'Model estimate of surface water runoff.' },
  { key: 'subsurface_runoff', display_name: 'Subsurface Runoff (Baseflow)', description: 'Water flow through the subsurface.', unit: 'mm/day', data_source: 'GLDAS Noah', available_coverage: '2000-01 to present', spatial_resolution: '0.25°', scientific_explanation: 'Model estimate of subsurface flow to streams.' },
  { key: 'terrestrial_water_storage', display_name: 'Terrestrial Water Storage Anomaly', description: 'Changes in total water stored on land.', unit: 'cm equivalent water height', data_source: 'GRACE / GRACE-FO', available_coverage: '2002-04 to present', spatial_resolution: '0.5°', scientific_explanation: 'Satellite observation of integrated land water storage changes.' },
  { key: 'ndvi', display_name: 'NDVI', description: 'Satellite-derived vegetation greenness index.', unit: 'Dimensionless', data_source: 'MODIS', available_coverage: '2000-02 to present', spatial_resolution: '1 km', scientific_explanation: 'Vegetation index derived from red and near-infrared reflectance.' },
  { key: 'evi', display_name: 'EVI', description: 'Enhanced satellite-derived vegetation index.', unit: 'Dimensionless', data_source: 'MODIS', available_coverage: '2000-02 to present', spatial_resolution: '1 km', scientific_explanation: 'Vegetation index designed to reduce atmospheric and soil effects.' },
];

function App() {
  const {
    ui,
    investigation,
    data,
    setActivePanel,
    setSidebarOpen,
    setLoading,
    setError,
    setAvailableVariables,
  } = useStore();

  const [backendConnected, setBackendConnected] = useState(false);

  // Load available variables on mount
  useEffect(() => {
    async function loadVariables() {
      try {
        const response = await fetch('/api/v1/variables');
        if (response.ok) {
          const variables = await response.json();
          setAvailableVariables(variables);
          setBackendConnected(true);
        } else {
          setAvailableVariables(FALLBACK_VARIABLES);
          setBackendConnected(false);
        }
      } catch (err) {
        setAvailableVariables(FALLBACK_VARIABLES);
        setBackendConnected(false);
      }
    }
    loadVariables();
  }, [setAvailableVariables, setError]);

  return (
    <div className="h-full min-h-0 w-full flex flex-col overflow-hidden">
      <Header onToggleSidebar={() => setSidebarOpen(!ui.sidebarOpen)} sidebarOpen={ui.sidebarOpen} backendConnected={backendConnected} />

      <main className="relative flex min-h-0 flex-1 overflow-hidden">
        {/* Left Sidebar - Investigation Controls */}
        {ui.sidebarOpen && (
          <aside className="z-10 w-80 min-h-0 flex-shrink-0 border-r border-hypnen-border bg-hypnen-dark transition-all duration-300 animate-slide-up">
            <InvestigationSidebar />
          </aside>
        )}

        {/* Center - Globe/Map View */}
        <section className="relative min-h-0 min-w-0 flex-1 overflow-hidden">
          {ui.activePanel === 'globe' && <GlobeView />}
          {ui.activePanel === 'map' && <MapView />}
        </section>

        {/* Right Panel - Results */}
        <aside className="z-10 hidden w-96 min-h-0 flex-shrink-0 border-l border-hypnen-border bg-hypnen-dark transition-all duration-300 animate-slide-up xl:block">
          <ResultsPanel />
        </aside>
      </main>

      {/* Loading Overlay */}
      {ui.loading && <LoadingOverlay message="Processing investigation..." />}

      {/* Error Toast */}
      {ui.error && <ErrorToast message={ui.error} onDismiss={() => setError(null)} />}
    </div>
  );
}

export default App;
