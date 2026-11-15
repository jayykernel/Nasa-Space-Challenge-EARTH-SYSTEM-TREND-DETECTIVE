import React from 'react';
import { useStore } from '../../store/useStore';

interface TimeRangeSelectorProps {
  timeRange: { start: string; end: string };
  temporalResolution: 'daily' | 'monthly' | 'annual' | 'seasonal';
  datasetId: string;
}

export function TimeRangeSelector({ timeRange, temporalResolution, datasetId }: TimeRangeSelectorProps) {
  const { setTimeRange, setTemporalResolution } = useStore();
  const isGpm = datasetId === 'gpm_imerg_monthly';
  const latestDate = isGpm ? '2025-09-30' : new Date().toISOString().slice(0, 10);
  const earliestDate = isGpm ? '2000-06-01' : '1900-01-01';
  const latestYear = Number(latestDate.slice(0, 4));

  // Quick preset time ranges
  const presets = [
    { label: 'Last 5 years', start: `${latestYear - 5}-10-01`, end: latestDate },
    { label: 'Last 10 years', start: `${latestYear - 10}-10-01`, end: latestDate },
    { label: 'Last 20 years', start: `${latestYear - 20}-10-01`, end: latestDate },
    { label: isGpm ? 'Full record (2000+)' : 'Last 30 years', start: isGpm ? earliestDate : `${latestYear - 30}-01-01`, end: latestDate },
  ];

  const handlePresetClick = (preset: typeof presets[0]) => {
    setTimeRange({ start: preset.start, end: preset.end });
  };

  const handleStartChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTimeRange({ ...timeRange, start: e.target.value });
  };

  const handleEndChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTimeRange({ ...timeRange, end: e.target.value });
  };

  const handleResolutionChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setTemporalResolution(e.target.value as any);
  };

  return (
    <div className="space-y-6">
      <div><p className="text-[10px] font-semibold uppercase tracking-[0.17em] text-sky-300/70">Step 3</p><h3 className="mt-1 text-[16px] font-semibold tracking-tight text-slate-100">Choose a time period</h3><p className="mt-1 text-[11px] text-slate-400">Monthly observations are available for both sources.</p></div>

      {/* Preset Buttons */}
      <div className="space-y-2">
        <label className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">Quick presets</label>
        <div className="grid grid-cols-2 gap-2">
          {presets.map((preset) => (
            <button
              key={preset.label}
              onClick={() => handlePresetClick(preset)}
              className={`rounded-xl border px-3 py-2.5 text-[11px] font-medium transition-all ${
                timeRange.start === preset.start && timeRange.end === preset.end
                  ? 'border-sky-300/30 bg-sky-300/[0.09] text-sky-100'
                  : 'border-white/[0.07] bg-white/[0.02] text-slate-400 hover:border-sky-300/20 hover:text-slate-100'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Custom Date Range */}
      <div className="space-y-4 rounded-2xl border border-white/[0.07] bg-white/[0.025] p-4">
        <label className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">Custom range</label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="mb-1.5 block text-[10px] font-medium text-slate-400">Start date</label>
            <input
              type="date"
              value={timeRange.start}
              onChange={handleStartChange}
              min={earliestDate}
              max={latestDate}
              className="w-full rounded-lg border border-white/[0.09] bg-[#080e19] px-2.5 py-2.5 text-[11px] text-slate-200 focus:border-sky-300/40 focus:outline-none"
            />
          </div>
          <div>
            <label className="mb-1.5 block text-[10px] font-medium text-slate-400">End date</label>
            <input
              type="date"
              value={timeRange.end}
              onChange={handleEndChange}
              min={earliestDate}
              max={latestDate}
              className="w-full rounded-lg border border-white/[0.09] bg-[#080e19] px-2.5 py-2.5 text-[11px] text-slate-200 focus:border-sky-300/40 focus:outline-none"
            />
          </div>
        </div>
        <div className="mt-2 flex items-center justify-between text-[10px] text-slate-500">
          <span>Selected span</span><span className="font-medium tabular-nums text-slate-300">{calculateTimespan(timeRange.start, timeRange.end)}</span>
        </div>
      </div>

      {/* Temporal Resolution */}
      <div className="space-y-2">
        <label className="text-[10px] font-semibold uppercase tracking-[0.16em] text-slate-500">Temporal resolution</label>
        <select
          value={temporalResolution}
          onChange={handleResolutionChange}
          className="w-full rounded-xl border border-white/[0.08] bg-white/[0.025] px-3 py-2.5 text-[11px] text-slate-200 focus:border-sky-300/40 focus:outline-none"
        >
          <option value="monthly">Monthly</option>
          <option value="seasonal">Seasonal (DJF, MAM, JJA, SON)</option>
          <option value="annual">Annual</option>
        </select>
        <p className="text-[11px] leading-relaxed text-slate-400">
          {temporalResolution === 'monthly' && 'Recommended for most climate trend analyses. Balances detail with statistical power.'}
          {temporalResolution === 'seasonal' && 'Useful for detecting seasonal shifts in climate patterns.'}
          {temporalResolution === 'annual' && 'Best for long-term trend detection with minimal noise.'}
        </p>
      </div>

      {/* Coverage Info */}
      <div className="rounded-2xl border border-sky-300/10 bg-sky-300/[0.035] p-3.5">
        <h4 className="mb-2 text-[11px] font-semibold text-sky-100">Coverage notes</h4>
        <ul className="space-y-1 text-[10px] text-slate-300">
          {isGpm ? <li>GPM IMERG Monthly V07B: Jun 2000 – Sep 2025</li> : <li>NOAA monthly summaries depend on nearby stations</li>}
        </ul>
        <p className="mt-2 text-[10px] leading-relaxed text-slate-500">
          {isGpm ? 'This monthly dataset does not provide daily observations. Choose a date range within the available archive to avoid missing recent months.' : 'NOAA monthly station records are limited to a ten-year window per request. Longer windows are retrieved in smaller chunks and may take more time.'}
        </p>
      </div>
    </div>
  );
}

function calculateTimespan(start: string, end: string): string {
  const startDate = new Date(start);
  const endDate = new Date(end);
  const diffMs = endDate.getTime() - startDate.getTime();
  const diffYears = diffMs / (1000 * 60 * 60 * 24 * 365.25);
  return `${diffYears.toFixed(1)} years`;
}
