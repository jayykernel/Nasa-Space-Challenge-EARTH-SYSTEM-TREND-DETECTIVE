import { useEffect, useRef, useState } from 'react';
import { useStore } from '../../store/useStore';
import * as echarts from 'echarts';
import 'echarts/dist/extension/bmap.min.js';

export function ResultsPanel() {
  const { data, ui } = useStore();
  const [linkCopied, setLinkCopied] = useState(false);
  const chartRef = useRef<HTMLDivElement>(null);
  const chartInstanceRef = useRef<echarts.ECharts | null>(null);
  const updateChartRef = useRef<((investigation: any) => void) | null>(null);

  // Initialize chart
  useEffect(() => {
    if (chartRef.current && !chartInstanceRef.current) {
      chartInstanceRef.current = echarts.init(chartRef.current, 'dark', {
        renderer: 'canvas',
      });

      const option = getEmptyChartOption();
      chartInstanceRef.current.setOption(option);

      window.addEventListener('resize', handleResize);
      return () => {
        window.removeEventListener('resize', handleResize);
        chartInstanceRef.current?.dispose();
        chartInstanceRef.current = null;
      };
    }
  }, []);

  const handleResize = () => {
    chartInstanceRef.current?.resize();
  };

  // Update chart when investigation results change
  useEffect(() => {
    if (chartInstanceRef.current && data.currentInvestigation) {
      updateChartRef.current?.(data.currentInvestigation);
    }
  }, [data.currentInvestigation]);

  const updateChart = (investigation: any) => {
    if (!chartInstanceRef.current) return;

    const timeSeries = investigation.time_series;
    if (!timeSeries || Object.keys(timeSeries).length === 0) {
      chartInstanceRef.current.setOption(getEmptyChartOption());
      return;
    }

    const series: any[] = [];
    const legendData: string[] = [];

    Object.entries(timeSeries as Record<string, any[]>).forEach(([variable, points]) => {
      if (!points || points.length === 0) return;

      const validPoints = points.filter((p: any) => p.value !== null && p.value !== undefined);
      if (validPoints.length === 0) return;

      legendData.push(variable);
      series.push({
        name: variable,
        type: 'line',
        data: validPoints.map((p: any) => [p.timestamp.split('T')[0], p.value]),
        smooth: true,
        symbol: 'circle',
        symbolSize: 4,
        lineStyle: { width: 2 },
        emphasis: { focus: 'series' },
      });

      // Add anomaly series if available
      const hasAnomalies = validPoints.some((p: any) => p.anomaly !== null && p.anomaly !== undefined);
      if (hasAnomalies) {
        series.push({
          name: `${variable} Anomaly`,
          type: 'bar',
          data: validPoints.map((p: any) => [p.timestamp.split('T')[0], p.anomaly ?? null]),
          itemStyle: { opacity: 0.5 },
          yAxisIndex: 1,
        });
      }
    });

    const option = {
      backgroundColor: 'transparent',
      legend: {
        data: legendData,
        top: 10,
        right: 10,
        textStyle: { color: '#e6edf3', fontSize: 11 },
        itemWidth: 16,
        itemHeight: 8,
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: 'rgba(22, 27, 34, 0.95)',
        borderColor: '#2a323c',
        borderWidth: 1,
        textStyle: { color: '#e6edf3' },
        formatter: (params: any) => {
          let html = `<div class="font-mono text-xs">${params[0].axisValue}</div>`;
          params.forEach((p: any) => {
            html += `<div style="color:${p.color};margin-top:4px">${p.seriesName}: ${p.value[1]?.toFixed(2) ?? 'N/A'}</div>`;
          });
          return html;
        },
      },
      grid: {
        top: 50,
        left: 50,
        right: 20,
        bottom: 50,
      },
      xAxis: {
        type: 'category',
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#2a323c' } },
        axisLabel: { color: '#8b949e', fontSize: 10, formatter: (value: string) => value.split('-').slice(0, 2).join('-') },
        axisTick: { show: false },
        splitLine: { show: false },
      },
      yAxis: [
        {
          type: 'value',
          name: 'Value',
          nameTextStyle: { color: '#8b949e', fontSize: 10 },
          axisLine: { lineStyle: { color: '#2a323c' } },
          axisLabel: { color: '#8b949e', fontSize: 10 },
          splitLine: { lineStyle: { color: '#2a323c', type: 'dashed' } },
        },
        {
          type: 'value',
          name: 'Anomaly',
          nameTextStyle: { color: '#8b949e', fontSize: 10 },
          axisLine: { lineStyle: { color: '#2a323c' } },
          axisLabel: { color: '#8b949e', fontSize: 10 },
          splitLine: { show: false },
        },
      ],
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        { type: 'slider', show: true, bottom: 10, height: 16, borderColor: '#2a323c', fillerColor: '#00d4ff33', handleStyle: { color: '#00d4ff' } },
      ],
      series,
    };

    chartInstanceRef.current.setOption(option, true);
  };
  updateChartRef.current = updateChart;

  const getEmptyChartOption = () => ({
    backgroundColor: 'transparent',
    title: {
      text: 'No Data',
      subtext: 'Run an investigation to see time series',
      left: 'center',
      top: 'center',
      textStyle: { color: '#8b949e', fontSize: 14 },
      subtextStyle: { color: '#8b949e', fontSize: 11 },
    },
    xAxis: { show: false },
    yAxis: { show: false },
  });

  // Render different views based on state
  if (ui.loading) {
    return (
      <div className="h-full flex flex-col bg-[#0a111d]">
        <div className="border-b border-white/[0.07] px-5 py-5">
          <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-sky-300/70">Workspace</p>
          <h2 className="flex items-center gap-2 text-[16px] font-semibold tracking-tight text-slate-100">
            <div className="w-5 h-5 spinner border-2 border-hypnen-border border-t-hypnen-cyan" />
            Analysis in Progress
          </h2>
        </div>
        <div className="flex-1 flex flex-col items-center justify-center p-4">
          <div className="w-16 h-16 spinner border-4 border-hypnen-border border-t-hypnen-cyan rounded-full mb-4" />
          <p className="text-hypnen-text text-center max-w-xs">
            {data.investigationStatus?.message || 'Processing your investigation...'}
          </p>
          <div className="w-full max-w-xs mt-4 h-2 bg-hypnen-border rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-hypnen-cyan to-hypnen-blue transition-all duration-300" style={{ width: `${data.investigationStatus?.progress || 0}%` }} />
          </div>
          <p className="text-xs text-hypnen-text-dim mt-2 text-center">
            {data.investigationStatus?.progress || 0}% complete
          </p>
        </div>
      </div>
    );
  }

  if (!data.currentInvestigation && !data.currentReport) {
    return (
      <div className="h-full flex flex-col">
        <div className="p-4 border-b border-hypnen-border">
          <h2 className="text-lg font-semibold text-hypnen-text flex items-center gap-2">
            <svg className="w-5 h-5 text-hypnen-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Investigation Results
          </h2>
        </div>
        <div className="flex flex-1 flex-col justify-between p-5">
          <div className="rounded-2xl border border-white/[0.07] bg-gradient-to-br from-sky-300/[0.06] via-transparent to-blue-400/[0.04] p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-sky-200/15 bg-sky-300/[0.08] text-sky-200">
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 19V5m0 14h16M7 15l4-4 3 2 5-6" /></svg>
              </div>
              <div>
                <p className="text-[13px] font-semibold text-slate-100">Your results will appear here</p>
                <p className="mt-1 text-[11px] leading-relaxed text-slate-400">Run an investigation to explore precipitation trends, data coverage, and statistical evidence.</p>
              </div>
            </div>
          </div>
          <div className="space-y-2.5 pb-1">
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">A clear path through the data</p>
            {['Choose a measurement source', 'Select a region on the globe', 'Set a time period and analyze'].map((step, index) => (
              <div key={step} className="flex items-center gap-3 rounded-xl border border-white/[0.055] bg-white/[0.02] px-3 py-2.5">
                <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-white/[0.045] text-[10px] font-semibold tabular-nums text-slate-400">0{index + 1}</span>
                <span className="text-[11px] text-slate-300">{step}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Results view
  const investigation = data.currentInvestigation;
  const report = data.currentReport;
  const trendStats = investigation?.trend_statistics || {};

  return (
      <div className="flex h-full flex-col overflow-hidden bg-[#0a111d]">
      {/* Header */}
      <div className="border-b border-white/[0.07] bg-[#0a111d]/90 px-5 py-4 backdrop-blur-xl">
        <p className="mb-1 text-[10px] font-semibold uppercase tracking-[0.18em] text-sky-300/70">Analysis workspace</p>
        <h2 className="flex items-center gap-2 text-[16px] font-semibold tracking-tight text-slate-100">
          <svg className="w-5 h-5 text-hypnen-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Investigation Results
        </h2>
        <p className="mt-1.5 text-[11px] text-slate-400">
          {investigation?.variables?.join(', ')} <span className="px-1 text-slate-600">·</span> {investigation?.time_range?.start} — {investigation?.time_range?.end}
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 space-y-4 overflow-y-auto p-4 sm:p-5">
        {investigation?.status === 'partial' && (
          <div className="rounded-lg border border-hypnen-yellow/40 bg-hypnen-yellow/10 p-3 text-xs text-hypnen-text" role="status">
            <p className="font-semibold text-hypnen-yellow">Partial coverage</p>
            <p className="mt-1 text-hypnen-text-dim">
              {investigation.data_quality?.missing_months?.length
                ? `No usable observations for ${investigation.data_quality.missing_months.join(', ')}.`
                : 'Some requested observations were unavailable.'}
            </p>
          </div>
        )}
        {/* Trend Summary Cards */}
        <div className="grid grid-cols-1 gap-3">
          {Object.entries(trendStats).map(([variable, stats]: [string, any]) => (
            <TrendSummaryCard key={variable} variable={variable} stats={stats} />
          ))}
        </div>

        {/* Time Series Chart */}
        <div className="card">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-hypnen-text">Time Series</h3>
            <div className="flex items-center gap-2">
              <span className="text-xs text-hypnen-text-dim">Units: {getUnits(investigation)}</span>
            </div>
          </div>
          <div ref={chartRef} className="h-64 w-full" />
        </div>

        {/* Statistical Details */}
        <div className="card">
          <h3 className="text-sm font-medium text-hypnen-text mb-3">Statistical Analysis</h3>
          <div className="space-y-3">
            {Object.entries(trendStats).map(([variable, stats]: [string, any]) => (
              <StatDetailsCard key={variable} variable={variable} stats={stats} />
            ))}
          </div>
        </div>

        {/* Scientific Report */}
        {report && (
          <div className="card">
            <h3 className="text-sm font-medium text-hypnen-text mb-3 flex items-center gap-2">
              <svg className="w-4 h-4 text-hypnen-cyan" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Scientific Report
            </h3>
            <div className="prose prose-invert max-w-none text-sm space-y-3">
              <div className="p-3 bg-hypnen-navy/50 rounded border border-hypnen-border">
                <h4 className="font-medium text-hypnen-text mb-2">{report.title}</h4>
                <p className="text-hypnen-text-dim text-xs mb-3">ID: {report.investigation_id?.slice(0, 8)}...</p>
                <div className="space-y-1 text-xs">
                  <div><strong>Region:</strong> {report.region_description}</div>
                  <div><strong>Period:</strong> {report.time_period}</div>
                  <div><strong>Variables:</strong> {report.variables?.join(', ')}</div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-hypnen-text mb-2">Interpretation</h4>
                <p className="text-hypnen-text-dim text-xs leading-relaxed">{report.interpretation}</p>
              </div>

              {report.scientific_limitations && report.scientific_limitations.length > 0 && (
                <div>
                  <h4 className="font-medium text-hypnen-text mb-2">Limitations</h4>
                  <ul className="text-hypnen-text-dim text-xs space-y-1 list-disc list-inside">
                    {report.scientific_limitations.slice(0, 5).map((lim: string, idx: number) => (
                      <li key={idx}>{lim}</li>
                    ))}
                  </ul>
                </div>
              )}

              <div className="pt-3 border-t border-hypnen-border">
                <h4 className="font-medium text-hypnen-text mb-2">Data Sources</h4>
                <p className="text-hypnen-text-dim text-xs">{report.data_source_citation}</p>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        {investigation && <div className="space-y-2 pt-4 border-t border-hypnen-border">
          <div className="flex gap-2">
            <a href={`/api/v1/analysis/${investigation.investigation_id}/report?format=pdf`} className="flex-1 rounded-lg border border-hypnen-border bg-hypnen-card px-3 py-2 text-center text-sm text-hypnen-text transition-colors hover:border-hypnen-cyan/30">Download PDF</a>
            <a href={`/api/v1/analysis/${investigation.investigation_id}/report?format=csv`} className="flex-1 rounded-lg border border-hypnen-border bg-hypnen-card px-3 py-2 text-center text-sm text-hypnen-text transition-colors hover:border-hypnen-cyan/30">Export CSV</a>
          </div>
          <button type="button" onClick={async () => {
            const link = new URL(window.location.href);
            link.searchParams.set('investigation', investigation.investigation_id);
            await navigator.clipboard.writeText(link.toString());
            setLinkCopied(true);
            window.setTimeout(() => setLinkCopied(false), 1800);
          }} className="w-full rounded-lg border border-hypnen-border px-3 py-2 text-xs text-hypnen-text-dim transition-colors hover:border-hypnen-cyan/30 hover:text-hypnen-text">
            {linkCopied ? 'Results link copied' : 'Copy results link'}
          </button>
        </div>}
      </div>
    </div>
  );
}

function TrendSummaryCard({ variable, stats }: { variable: string; stats: any }) {
  const direction = stats.trend_direction || 'insufficient_data';
  const significant = stats.is_significant === true;
  const slope = stats.sens_slope?.slope ?? stats.linear_regression?.slope;
  const pValue = stats.mann_kendall?.p_value ?? stats.linear_regression?.p_value;
  const rSquared = stats.linear_regression?.r_squared;

  const getDirectionColor = () => {
    if (!significant) return 'text-hypnen-yellow';
    if (direction === 'increasing') return 'text-hypnen-green';
    if (direction === 'decreasing') return 'text-hypnen-red';
    return 'text-hypnen-yellow';
  };

  const getDirectionIcon = () => {
    if (!significant) return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
    );
    if (direction === 'increasing') return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 10l7-7m0 0l7 7m-7-7v18" />
      </svg>
    );
    return (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V5" />
      </svg>
    );
  };

  const getDirectionLabel = () => {
    if (stats.status === 'insufficient_data') return 'Insufficient Data';
    if (!significant) return 'Not Significant';
    if (direction === 'increasing') return 'Increasing';
    if (direction === 'decreasing') return 'Decreasing';
    return 'No Trend';
  };

  return (
    <div className={`card p-4 ${significant ? 'border-hypnen-cyan/30' : ''}`}>
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="text-xs font-medium text-hypnen-text-dim uppercase tracking-wider">{formatVariableName(variable)}</p>
          <p className="text-sm font-semibold text-hypnen-text mt-1 capitalize">{variable.replace('_', ' ')}</p>
        </div>
        <div className={`flex items-center gap-1 ${getDirectionColor()}`}>
          {getDirectionIcon()}
          <span className="text-xs font-medium">{getDirectionLabel()}</span>
        </div>
      </div>

      <div className="space-y-2 text-xs">
        <div className="flex justify-between">
          <span className="text-hypnen-text-dim">Sen's Slope</span>
          <span className="font-mono text-hypnen-text">{typeof slope === 'number' ? `${slope.toExponential(3)} ${stats.sens_slope?.unit || 'per year'}` : 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-hypnen-text-dim">P-value (MK)</span>
          <span className="font-mono text-hypnen-text">{typeof pValue === 'number' ? (pValue < 0.001 ? '< 0.001' : pValue.toFixed(3)) : 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-hypnen-text-dim">R² (Linear)</span>
          <span className="font-mono text-hypnen-text">{typeof rSquared === 'number' ? rSquared.toFixed(3) : 'N/A'}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-hypnen-text-dim">Observations</span>
          <span className="font-mono text-hypnen-text">{stats.linear_regression?.n_obs ?? stats.descriptive_stats?.n_obs ?? 'N/A'}</span>
        </div>
      </div>
    </div>
  );
}

function StatDetailsCard({ variable, stats }: { variable: string; stats: any }) {
  const mk = stats.mann_kendall || {};
  const lr = stats.linear_regression || {};
  const sens = stats.sens_slope || {};
  const desc = stats.descriptive_stats || {};

  return (
    <div className="p-3 bg-hypnen-navy/50 rounded border border-hypnen-border">
      <h4 className="font-medium text-hypnen-text mb-3 capitalize">{variable.replace('_', ' ')}</h4>
      <div className="grid grid-cols-2 gap-3 text-xs">
        <StatRow label="Mann-Kendall" value={`${mk.trend || 'N/A'} (τ=${mk.tau?.toFixed(3) || 'N/A'})`} />
        <StatRow label="MK P-value" value={typeof mk.p_value === 'number' ? (mk.p_value < 0.001 ? '< 0.001' : mk.p_value.toFixed(4)) : 'N/A'} />
        <StatRow label="Seasonal MK" value={stats.seasonal_mann_kendall?.trend || 'N/A'} />
        <StatRow label="Seasonal P-value" value={stats.seasonal_mann_kendall?.p_value?.toFixed(4) || 'N/A'} />
        <StatRow label="Linear Slope" value={`${lr.slope?.toExponential(3) || 'N/A'} /yr`} />
        <StatRow label="Linear P-value" value={lr.p_value?.toFixed(4) || 'N/A'} />
        <StatRow label="R²" value={lr.r_squared?.toFixed(3) || 'N/A'} />
        <StatRow label="Sen's Slope" value={`${sens.slope?.toExponential(3) || 'N/A'} /yr`} />
        <StatRow label="Sen's CI" value={typeof sens.ci_lower === 'number' && typeof sens.ci_upper === 'number' ? `[${sens.ci_lower.toExponential(2)}, ${sens.ci_upper.toExponential(2)}]` : 'N/A'} />
        <StatRow label="Mean" value={desc.mean?.toFixed(3) || 'N/A'} />
        <StatRow label="Std Dev" value={desc.std?.toFixed(3) || 'N/A'} />
        <StatRow label="Missing %" value={`${desc.missing_pct?.toFixed(1) || '0'}%`} />
        <StatRow label="Observations" value={desc.n_obs || 0} />
        <StatRow label="Autocorr." value={stats.autocorrelation?.significant_autocorr ? 'Yes (significant)' : 'No'} />
        <StatRow label="Ljung-Box p" value={stats.autocorrelation?.lb_pvalue?.toFixed(3) || 'N/A'} />
      </div>
    </div>
  );
}

function StatRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-hypnen-text-dim">{label}</span>
      <span className="font-mono text-hypnen-text">{value}</span>
    </div>
  );
}

function formatVariableName(variable: string): string {
  const names: Record<string, string> = {
    precipitation: 'Rainfall',
    temperature: 'Temperature',
    specific_humidity: 'Spec. Humidity',
    relative_humidity: 'Rel. Humidity',
    soil_moisture: 'Soil Moisture',
    evapotranspiration: 'Evapotranspiration',
    runoff: 'Runoff',
    subsurface_runoff: 'Baseflow',
    terrestrial_water_storage: 'TWS',
    ndvi: 'NDVI',
    evi: 'EVI',
  };
  return names[variable] || variable;
}

function getUnits(investigation: any): string {
  if (investigation?.units) return Object.values(investigation.units).join(', ');
  const units: Record<string, string> = {
    precipitation: 'mm/day',
    temperature: '°C',
    specific_humidity: 'kg/kg',
    relative_humidity: '%',
    soil_moisture: 'm³/m³',
    evapotranspiration: 'mm/day',
    runoff: 'mm/day',
    subsurface_runoff: 'mm/day',
    terrestrial_water_storage: 'cm',
    ndvi: 'index',
    evi: 'index',
  };
  const vars = investigation?.variables || [];
  return vars.map((v: string) => units[v] || 'units').join(', ');
}
