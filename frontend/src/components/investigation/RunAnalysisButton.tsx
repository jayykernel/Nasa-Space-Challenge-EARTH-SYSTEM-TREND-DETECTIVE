import React from 'react';
import { useStore } from '../../store/useStore';

export function RunAnalysisButton() {
  const {
    investigation,
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
      // Start investigation
      const response = await fetch('/api/v1/analysis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start investigation');
      }

      const { investigation_id } = await response.json();

      // Poll for status
      await pollInvestigationStatus(investigation_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
      setLoading(false);
    }
  };

  const pollInvestigationStatus = async (investigationId: string) => {
    const maxAttempts = 300; // 5 minutes at 1 second intervals
    let attempts = 0;

    while (attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      attempts++;

      try {
        const response = await fetch(`/api/v1/analysis/${investigationId}/status`);
        if (!response.ok) throw new Error('Failed to get status');

        const status = await response.json();
        setInvestigationStatus(status);

        if (status.status === 'completed') {
          // Fetch results
          const resultsResponse = await fetch(`/api/v1/analysis/${investigationId}/results`);
          if (resultsResponse.ok) {
            const results = await resultsResponse.json();
            setInvestigationResults(results);
          }

          // Fetch report
          const reportResponse = await fetch(`/api/v1/analysis/${investigationId}/report`);
          if (reportResponse.ok) {
            const report = await reportResponse.json();
            setInvestigationReport(report);
          }

          setLoading(false);
          setActivePanel('results');
          return;
        }

        if (status.status === 'failed') {
          setLoading(false);
          setError(status.message || 'Investigation failed');
          return;
        }

        if (status.status === 'cancelled') {
          setLoading(false);
          return;
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }

    setLoading(false);
    setError('Investigation timed out. Please try again.');
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-hypnen-text">Run Analysis</h3>
      </div>

      {/* Validation Status */}
      <div className="space-y-3">
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
        className={`w-full py-4 px-6 rounded-lg font-semibold text-lg transition-all flex items-center justify-center gap-3 ${
          canRun && !ui.loading
            ? 'bg-gradient-to-r from-hypnen-cyan to-hypnen-blue text-hypnen-navy hover:from-hypnen-cyan/90 hover:to-hypnen-blue/90 glow-cyan'
            : 'bg-hypnen-border text-hypnen-text-dim cursor-not-allowed'
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
            <span>Run Analysis</span>
          </>
        )}
      </button>

      {/* Progress Display */}
      {ui.loading && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-hypnen-text-dim">Progress</span>
            <span className="text-hypnen-cyan font-mono">{ui.data.investigationStatus?.progress || 0}%</span>
          </div>
          <div className="w-full h-2 bg-hypnen-border rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-hypnen-cyan to-hypnen-blue transition-all duration-300"
              style={{ width: `${ui.data.investigationStatus?.progress || 0}%` }}
            />
          </div>
          <p className="text-xs text-hypnen-text-dim text-center">
            {ui.data.investigationStatus?.message || 'Processing...'}
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
            <span>Backend searches NASA catalogs for matching granules</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-hypnen-cyan flex-shrink-0 mt-1.5" />
            <span>Downloads and processes NetCDF/HDF5 files</span>
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