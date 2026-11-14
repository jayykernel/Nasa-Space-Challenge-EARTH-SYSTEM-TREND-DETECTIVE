import React from 'react';
import { useStore } from '../../store/useStore';

interface TimeRangeSelectorProps {
  timeRange: { start: string; end: string };
  temporalResolution: 'daily' | 'monthly' | 'annual' | 'seasonal';
}

export function TimeRangeSelector({ timeRange, temporalResolution }: TimeRangeSelectorProps) {
  const { setTimeRange, setTemporalResolution } = useStore();

  // Quick preset time ranges
  const presets = [
    { label: 'Last 5 years', start: '2020-01-01', end: '2025-12-31' },
    { label: 'Last 10 years', start: '2015-01-01', end: '2025-12-31' },
    { label: 'Last 20 years', start: '2005-01-01', end: '2025-12-31' },
    { label: 'Full record (2000+)', start: '2000-01-01', end: '2025-12-31' },
    { label: 'Satellite era (1980+)', start: '1980-01-01', end: '2025-12-31' },
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
      <h3 className="text-lg font-semibold text-hypnen-text">Time Range</h3>

      {/* Preset Buttons */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-hypnen-text-dim uppercase tracking-wider">Quick Presets</label>
        <div className="grid grid-cols-2 gap-2">
          {presets.map((preset) => (
            <button
              key={preset.label}
              onClick={() => handlePresetClick(preset)}
              className={`px-3 py-2 rounded-lg border text-sm transition-all ${
                timeRange.start === preset.start && timeRange.end === preset.end
                  ? 'bg-hypnen-cyan/20 border-hypnen-cyan text-hypnen-cyan'
                  : 'border-hypnen-border text-hypnen-text-dim hover:border-hypnen-cyan/30 hover:text-hypnen-text hover:bg-hypnen-card'
              }`}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Custom Date Range */}
      <div className="space-y-4 p-4 bg-hypnen-card border border-hypnen-border rounded-lg">
        <label className="text-xs font-medium text-hypnen-text-dim uppercase tracking-wider">Custom Range</label>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-hypnen-text-dim mb-1">Start Date</label>
            <input
              type="date"
              value={timeRange.start}
              onChange={handleStartChange}
              min="1980-01-01"
              max="2025-12-31"
              className="w-full px-3 py-2 bg-hypnen-navy border border-hypnen-border rounded-lg text-hypnen-text focus:border-hypnen-cyan focus:outline-none focus:ring-1 focus:ring-hypnen-cyan"
            />
          </div>
          <div>
            <label className="block text-xs text-hypnen-text-dim mb-1">End Date</label>
            <input
              type="date"
              value={timeRange.end}
              onChange={handleEndChange}
              min="1980-01-01"
              max="2025-12-31"
              className="w-full px-3 py-2 bg-hypnen-navy border border-hypnen-border rounded-lg text-hypnen-text focus:border-hypnen-cyan focus:outline-none focus:ring-1 focus:ring-hypnen-cyan"
            />
          </div>
        </div>
        <div className="text-xs text-hypnen-text-dim mt-2">
          Span: {calculateTimespan(timeRange.start, timeRange.end)}
        </div>
      </div>

      {/* Temporal Resolution */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-hypnen-text-dim uppercase tracking-wider">Temporal Resolution</label>
        <select
          value={temporalResolution}
          onChange={handleResolutionChange}
          className="w-full px-3 py-2 bg-hypnen-card border border-hypnen-border rounded-lg text-hypnen-text focus:border-hypnen-cyan focus:outline-none focus:ring-1 focus:ring-hypnen-cyan"
        >
          <option value="daily">Daily (where available)</option>
          <option value="monthly">Monthly</option>
          <option value="seasonal">Seasonal (DJF, MAM, JJA, SON)</option>
          <option value="annual">Annual</option>
        </select>
        <p className="text-xs text-hypnen-text-dim">
          {temporalResolution === 'monthly' && 'Recommended for most climate trend analyses. Balances detail with statistical power.'}
          {temporalResolution === 'seasonal' && 'Useful for detecting seasonal shifts in climate patterns.'}
          {temporalResolution === 'annual' && 'Best for long-term trend detection with minimal noise.'}
          {temporalResolution === 'daily' && 'High frequency data. Requires large datasets and careful handling of autocorrelation.'}
        </p>
      </div>

      {/* Coverage Info */}
      <div className="p-3 bg-hypnen-blue/10 border border-hypnen-blue/30 rounded-lg">
        <h4 className="text-sm font-medium text-hypnen-blue mb-2">Dataset Coverage Notes</h4>
        <ul className="text-xs text-hypnen-text space-y-1">
          <li>• GPM IMERG: 2000-06 to present</li>
          <li>• MERRA-2: 1980-01 to present</li>
          <li>• GLDAS Noah: 2000-01 to present</li>
          <li>• GRACE/GRACE-FO: 2002-04 to present (gap 2017-2018)</li>
          <li>• MODIS: 2000-02 to present</li>
        </ul>
        <p className="text-xs text-hypnen-text-dim mt-2">
          Time ranges outside dataset coverage will return no data.
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