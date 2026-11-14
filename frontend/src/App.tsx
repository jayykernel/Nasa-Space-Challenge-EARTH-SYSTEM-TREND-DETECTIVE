import { useEffect, useState } from 'react';
import { useStore } from './store/useStore';
import { InvestigationSidebar } from './components/investigation/InvestigationSidebar';
import { GlobeView } from './components/globe/GlobeView';
import { MapView } from './components/maps/MapView';
import { ResultsPanel } from './components/dashboard/ResultsPanel';
import { Header } from './components/layout/Header';
import { LoadingOverlay } from './components/ui/LoadingOverlay';
import { ErrorToast } from './components/ui/ErrorToast';

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

  const [variablesLoaded, setVariablesLoaded] = useState(false);

  // Load available variables on mount
  useEffect(() => {
    async function loadVariables() {
      try {
        const response = await fetch('/api/v1/variables');
        if (response.ok) {
          const variables = await response.json();
          setAvailableVariables(variables);
          setVariablesLoaded(true);
        } else {
          setError('Failed to load available variables');
        }
      } catch (err) {
        setError('Failed to connect to backend API');
      }
    }
    loadVariables();
  }, [setAvailableVariables, setError]);

  return (
    <div className="h-full w-full flex flex-col overflow-hidden">
      <Header onToggleSidebar={() => setSidebarOpen(!ui.sidebarOpen)} sidebarOpen={ui.sidebarOpen} />

      <main className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar - Investigation Controls */}
        {ui.sidebarOpen && (
          <aside className="w-80 flex-shrink-0 border-r border-hypnen-border bg-hypnen-dark transition-all duration-300 animate-slide-up z-10">
            <InvestigationSidebar />
          </aside>
        )}

        {/* Center - Globe/Map View */}
        <section className="flex-1 relative min-w-0 overflow-hidden">
          {ui.activePanel === 'globe' && <GlobeView />}
          {ui.activePanel === 'map' && <MapView />}
        </section>

        {/* Right Panel - Results */}
        <aside className="w-96 flex-shrink-0 border-l border-hypnen-border bg-hypnen-dark transition-all duration-300 animate-slide-up z-10">
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