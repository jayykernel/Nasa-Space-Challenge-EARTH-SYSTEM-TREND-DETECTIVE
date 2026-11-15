import { useStore } from '../../store/useStore';
import { api } from '../../services/api';

export function RunAnalysisButton() {
  const {
    investigation,
    data,
    ui,
    buildInvestigationRequest,
    setLoading,
    setError,
    setInvestigationStatus,
    setInvestigationResults,
    setInvestigationReport,
    setActivePanel,
  } = useStore();

  const canRun = investigation.variables.length > 0 && investigation.geometry !== null;
  const usesNoaa = investigation.datasetId === 'noaa_ghcn_monthly_precipitation';

  const handleRunAnalysis = async () => {
    const request = buildInvestigationRequest();
    if (!request) {
      setError('Please select at least one variable and a geographical region');
      return;
    }

    setLoading(true);
    setError(null);
    setInvestigationStatus({
      investigation_id: '',
      status: 'queued',
      progress: 0,
      message: 'Starting investigation...',
    });

    try {
      const created = await api.startInvestigation(request);
      const results = await api.pollInvestigation(created.investigation_id, setInvestigationStatus);
      setInvestigationResults(results);
      setLoading(false);
      setActivePanel('results');
      try {
        const report = await api.getInvestigationReport(created.investigation_id);
        setInvestigationReport(report);
      } catch {
        setError('Your measurements are ready. The written report could not be loaded.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><p className="text-[10px] font-semibold uppercase tracking-[0.17em] text-sky-300/70">Step 4</p><h3 className="mt-1 text-[16px] font-semibold tracking-tight text-slate-100">Review and analyze</h3></div>
      </div>

      {/* Validation Status */}
      <div className="space-y-2.5">
        <div className={`flex items-center gap-3 p-3 rounded-lg ${
          investigation.variables.length > 0
            ? 'bg-hypnen-green/10 border border-hypnen-green/30'
            : 'bg-hypnen-red/10 border border-hypnen-red/30'
        }`}>
          <svg className={`w-5 h-5 ${investigation.variables.length > 0 ? 'text-hypnen-green' : 'text-hypnen-red'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={investigation.variables.length > 0 ? "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" : "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m-2 2l2 2m-2 2l-2 2m-2-2l-2-2"} />
          </svg>
          <div>
            <p className="text-sm font-medium text-hypnen-text">Variables Selected</p>
            <p className="text-xs text-hypnen-text-dim">
              {investigation.variables.length > 0
                ? `${investigation.variables.length} variable(s) ready`
                : 'Select at least one variable'}
            </p>
          </div>
        </div>

        <div className={`flex items-center gap-3 p-3 rounded-lg ${
          investigation.geometry !== null
            ? 'bg-hypnen-green/10 border border-hypnen-green/30'
            : 'bg-hypnen-red/10 border border-hypnen-red/30'
        }`}>
          <svg className={`w-5 h-5 ${investigation.geometry !== null ? 'text-hypnen-green' : 'text-hypnen-red'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={investigation.geometry !== null ? "M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" : "M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l-2-2m-2 2l-2-2m2 2l2 2m-2 2l2 2m-2 2l-2 2m-2-2l-2-2"} />
          </svg>
          <div>
            <p className="text-sm font-medium text-hypnen-text">Region Selected</p>
            <p className="text-xs text-hypnen-text-dim">
              {investigation.geometry !== null
                ? `Geometry: ${investigation.geometry.type}`
                : 'Select a geographical region on the globe'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 p-3 rounded-lg bg-hypnen-blue/10 border border-hypnen-blue/30">
          <svg className="w-5 h-5 text-hypnen-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <p className="text-sm font-medium text-hypnen-text">Time Range</p>
            <p className="text-xs text-hypnen-text-dim">
              {investigation.timeRange.start} to {investigation.timeRange.end} ({investigation.temporalResolution})
            </p>
          </div>
        </div>
      </div>

      {/* Run Button */}
      <button
        onClick={handleRunAnalysis}
        disabled={!canRun || ui.loading}
        className={`flex w-full items-center justify-center gap-2.5 rounded-xl px-5 py-3.5 text-[13px] font-semibold transition-all ${
          canRun && !ui.loading
            ? 'border border-sky-200/25 bg-gradient-to-r from-sky-300 to-cyan-300 text-slate-950 shadow-[0_10px_28px_rgba(14,165,233,0.16)] hover:brightness-105'
            : 'cursor-not-allowed border border-white/[0.07] bg-white/[0.05] text-slate-500'
        }`}
      >
        {ui.loading ? (
          <>
            <div className="w-5 h-5 spinner border-2 border-hypnen-navy/30 border-t-hypnen-navy" />
            <span>Running Investigation...</span>
          </>
        ) : (
          <>
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>Run precipitation analysis</span>
          </>
        )}
      </button>

      {/* Progress Display */}
      {ui.loading && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-hypnen-text-dim">Progress</span>
            <span className="text-hypnen-cyan font-mono">{data.investigationStatus?.progress || 0}%</span>
          </div>
          <div className="w-full h-2 bg-hypnen-border rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-hypnen-cyan to-hypnen-blue transition-all duration-300"
              style={{ width: `${data.investigationStatus?.progress || 0}%` }}
            />
          </div>
          <p className="text-xs text-hypnen-text-dim text-center">
            {data.investigationStatus?.message || 'Processing...'}
          </p>
        </div>
      )}

      {/* What happens next */}
      <div className="p-4 bg-hypnen-card border border-hypnen-border rounded-lg">
        <h4 className="text-sm font-medium text-hypnen-text mb-3 flex items-center gap-2">
          <svg className="w-4 h-4 text-hypnen-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          What happens next
        </h4>
        <ul className="text-xs text-hypnen-text-dim space-y-2">
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-hypnen-cyan flex-shrink-0 mt-1.5" />
            <span>{usesNoaa ? 'Finds NOAA reporting stations inside your region' : 'Finds NASA satellite data for your region'}</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-hypnen-cyan flex-shrink-0 mt-1.5" />
            <span>{usesNoaa ? 'Retrieves and checks monthly station observations' : 'Retrieves and checks satellite data files'}</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-hypnen-cyan flex-shrink-0 mt-1.5" />
            <span>Extracts measurements for your region</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-hypnen-cyan flex-shrink-0 mt-1.5" />
            <span>Performs statistical trend analysis (Mann-Kendall, Sen's slope, linear regression)</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-hypnen-cyan flex-shrink-0 mt-1.5" />
            <span>Generates scientific report with visualizations</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
