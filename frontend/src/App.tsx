import { lazy, Suspense, useEffect, useState } from 'react';
import { useStore } from './store/useStore';
import { InvestigationSidebar } from './components/investigation/InvestigationSidebar';
import { ResultsPanel } from './components/dashboard/ResultsPanel';
import { Header } from './components/layout/Header';
import { LoadingOverlay } from './components/ui/LoadingOverlay';
import { ErrorToast } from './components/ui/ErrorToast';
import type { VariableInfo } from './types';
import { api } from './services/api';
import type { InvestigationResults as AppInvestigationResults } from './types';

const GlobeView = lazy(() => import('./components/globe/GlobeView').then((module) => ({ default: module.GlobeView })));
const MapView = lazy(() => import('./components/maps/MapView').then((module) => ({ default: module.MapView })));

const FALLBACK_VARIABLES: VariableInfo[] = [
  { key: 'precipitation', display_name: 'Rainfall / Precipitation', description: 'Compare NASA satellite measurements with NOAA station records.', unit: 'Dataset units', data_source: 'NASA GPM IMERG or NOAA GHCN', available_coverage: 'Dataset-specific', spatial_resolution: 'Global 0.1° grid or station network', scientific_explanation: 'Select a global gridded satellite product or station observations for the selected region.', dataset_ids: ['gpm_imerg_monthly', 'noaa_ghcn_monthly_precipitation'] },
];

function App() {
  const {
    ui,
    data,
    setSidebarOpen,
    setError,
    setAvailableVariables,
    setLoading,
    setInvestigationStatus,
    setInvestigationResults,
    setInvestigationReport,
    setGeometry,
    setTimeRange,
    setVariables,
    setDatasetId,
    setActivePanel,
  } = useStore();

  const [backendConnected, setBackendConnected] = useState(false);

  // Load available variables on mount
  useEffect(() => {
    async function loadVariables() {
      try {
        const variables = await api.getVariables();
        setAvailableVariables(variables);
        setBackendConnected(true);
      } catch {
        setAvailableVariables(FALLBACK_VARIABLES);
        setBackendConnected(false);
      }
    }
    loadVariables();
  }, [setAvailableVariables, setError]);

  // A saved investigation can be reopened directly from its shareable URL.
  useEffect(() => {
    const investigationId = new URLSearchParams(window.location.search).get('investigation');
    if (!investigationId) return;
    const savedId = investigationId;
    let cancelled = false;
    async function loadSavedInvestigation() {
      setLoading(true);
      try {
        const status = await api.getInvestigationStatus(savedId);
        if (cancelled) return;
        setInvestigationStatus(status);
        if (status.status === 'completed' || status.status === 'partial') {
          const [results, report] = await Promise.all([
            api.getInvestigationResults(savedId),
            api.getInvestigationReport(savedId),
          ]);
          if (cancelled) return;
          setInvestigationResults(results as unknown as AppInvestigationResults);
          setInvestigationReport(report);
          if (results.region) setGeometry(results.region);
          if (report.region_description) window.dispatchEvent(new CustomEvent('globe-region-name', { detail: { name: report.region_description } }));
          if (results.time_range) setTimeRange(results.time_range);
          setVariables(results.variables);
          if (results.dataset?.id) setDatasetId(results.dataset.id);
          setActivePanel('results');
        }
      } catch (error) {
        if (!cancelled) setError(error instanceof Error ? error.message : 'Could not load the saved investigation');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void loadSavedInvestigation();
    return () => { cancelled = true; };
  }, [setActivePanel, setDatasetId, setError, setGeometry, setInvestigationReport, setInvestigationResults, setInvestigationStatus, setLoading, setTimeRange, setVariables]);

  return (
    <div className="flex h-full min-h-0 w-full flex-col overflow-hidden bg-[#070c14]">
      <Header onToggleSidebar={() => setSidebarOpen(!ui.sidebarOpen)} sidebarOpen={ui.sidebarOpen} backendConnected={backendConnected} activePanel={ui.activePanel} onPanelChange={setActivePanel} hasResults={Boolean(data.currentInvestigation)} />

      <main className="relative flex min-h-0 flex-1 overflow-hidden">
        {/* Left Sidebar - Investigation Controls */}
        {ui.sidebarOpen && (
          <aside className="z-10 w-[min(360px,88vw)] min-h-0 flex-shrink-0 border-r border-white/[0.08] bg-[#0a111d] transition-all duration-300 animate-slide-up xl:w-[352px]">
            <InvestigationSidebar />
          </aside>
        )}

        {/* Center - Globe/Map View */}
        <section className="relative min-h-0 min-w-0 flex-1 overflow-hidden">
          {ui.activePanel === 'globe' && <Suspense fallback={<ViewLoading label="Preparing the 3D globe…" />}><GlobeView /></Suspense>}
          {ui.activePanel === 'map' && <Suspense fallback={<ViewLoading label="Preparing the map…" />}><MapView /></Suspense>}
          {ui.activePanel === 'results' && <div className="h-full overflow-hidden"><ResultsPanel /></div>}
        </section>

        {/* Right Panel - Results */}
        <aside className={`z-10 hidden w-[400px] min-h-0 flex-shrink-0 border-l border-white/[0.08] bg-[#0a111d] transition-all duration-300 animate-slide-up xl:block ${ui.activePanel === 'results' ? '!hidden' : ''}`}>
          <ResultsPanel />
        </aside>
      </main>

      {/* Loading Overlay */}
      {ui.loading && <LoadingOverlay progress={data.investigationStatus?.progress ?? 0} message={data.investigationStatus?.message || 'Starting the investigation…'} />}

      {/* Error Toast */}
      {ui.error && <ErrorToast message={ui.error} onDismiss={() => setError(null)} />}
    </div>
  );
}

function ViewLoading({ label }: { label: string }) {
  return <div className="flex h-full items-center justify-center bg-[#030812] text-sm text-slate-300"><span className="mr-3 h-5 w-5 animate-spin rounded-full border-2 border-slate-600 border-t-sky-400" />{label}</div>;
}

export default App;
