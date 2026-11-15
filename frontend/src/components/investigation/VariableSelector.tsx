import React from 'react';
import { useStore } from '../../store/useStore';
import type { VariableInfo } from '../../types';

interface VariableSelectorProps {
  availableVariables: VariableInfo[];
  selectedVariables: string[];
  selectedDatasetId: string;
}

export function VariableSelector({ availableVariables, selectedVariables, selectedDatasetId }: VariableSelectorProps) {
  const { setVariables, setDatasetId } = useStore();

  // Group variables by category
  const atmosphericVars = availableVariables.filter(v =>
    ['temperature', 'specific_humidity', 'relative_humidity'].includes(v.key)
  );
  const hydrologicalVars = availableVariables.filter(v =>
    ['precipitation', 'soil_moisture', 'evapotranspiration', 'runoff', 'subsurface_runoff', 'terrestrial_water_storage'].includes(v.key)
  );
  const vegetationVars = availableVariables.filter(v =>
    ['ndvi', 'evi'].includes(v.key)
  );

  const toggleVariable = (key: string) => {
    setVariables(selectedVariables.includes(key) ? [] : [key]);
    if (!selectedVariables.includes(key)) {
      const selected = availableVariables.find((variable) => variable.key === key);
      if (selected?.dataset_ids?.length) setDatasetId(selected.dataset_ids[0]);
    }
  };

  const VariableGroup = ({ title, variables }: { title: string; variables: VariableInfo[] }) => (
    <div className="space-y-3">
      <h4 className="border-b border-white/[0.07] pb-2 text-[10px] font-semibold uppercase tracking-[0.17em] text-slate-500">{title}</h4>
      {variables.map((variable) => (
        <button
          key={variable.key}
          onClick={() => toggleVariable(variable.key)}
          className={`w-full rounded-xl border p-3.5 text-left transition-all duration-200 ${
            selectedVariables.includes(variable.key)
              ? 'border-sky-300/35 bg-gradient-to-br from-sky-300/[0.10] to-blue-400/[0.04] shadow-[0_8px_24px_rgba(14,165,233,0.06)]'
              : 'border-white/[0.08] bg-white/[0.025] hover:border-sky-300/20 hover:bg-white/[0.045]'
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-[13px] font-semibold text-slate-100">{variable.display_name}</span>
                {selectedVariables.includes(variable.key) && (
                  <span className="h-1.5 w-1.5 rounded-full bg-sky-300 shadow-[0_0_8px_rgba(125,211,252,0.7)]" />
                )}
              </div>
              <p className="mt-1.5 line-clamp-2 text-[11px] leading-relaxed text-slate-400">{variable.description}</p>
              <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[10px] text-slate-500">
                <span className="flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  {variable.unit}
                </span>
                <span className="flex items-center gap-1">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  {variable.spatial_resolution}
                </span>
              </div>
            </div>
            <div className={`flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-md border transition ${
              selectedVariables.includes(variable.key)
                ? 'border-sky-200/50 bg-sky-300 text-slate-950'
                : 'border-white/15 bg-black/10 text-slate-500'
            }`}>
              {selectedVariables.includes(variable.key) && (
                <svg className="w-4 h-4 text-hypnen-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </div>
          </div>
        </button>
      ))}
    </div>
  );

  if (availableVariables.length === 0) {
    return (
      <div className="card text-center py-8">
        <svg className="w-12 h-12 text-hypnen-text-dim mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
        <p className="text-hypnen-text-dim">Loading available variables...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><p className="text-[10px] font-semibold uppercase tracking-[0.17em] text-sky-300/70">Step 1</p><h3 className="mt-1 text-[16px] font-semibold tracking-tight text-slate-100">Choose your data</h3></div>
        <span className="rounded-full border border-white/[0.08] bg-white/[0.03] px-2 py-1 text-[10px] text-slate-400">
          {selectedVariables.length} of 1 selected
        </span>
      </div>

      <div className="space-y-6">
        {hydrologicalVars.length > 0 && (
          <VariableGroup title="Hydrological" variables={hydrologicalVars} />
        )}
        {atmosphericVars.length > 0 && (
          <VariableGroup title="Atmospheric" variables={atmosphericVars} />
        )}
        {vegetationVars.length > 0 && (
          <VariableGroup title="Vegetation" variables={vegetationVars} />
        )}
      </div>

      {selectedVariables.length === 1 && (() => {
        const selected = availableVariables.find((variable) => variable.key === selectedVariables[0]);
        const ids = selected?.dataset_ids || [];
        if (ids.length < 2) return null;
        return <section className="card space-y-3 p-4" aria-labelledby="source-choice-title">
          <div><p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-sky-300/70">Measurement</p><h4 id="source-choice-title" className="mt-1 text-[13px] font-semibold text-slate-100">Choose a data source</h4><p className="mt-1 text-[11px] leading-relaxed text-slate-400">Satellite estimates cover the globe. Station observations depend on local reporting sites.</p></div>
          {ids.map((id) => {
            const isSatellite = id === 'gpm_imerg_monthly';
            const title = isSatellite ? 'NASA GPM IMERG' : 'NOAA station observations';
            const detail = isSatellite
              ? 'Global 0.1° grid · monthly mean rate · through Sep 2025'
              : 'Monthly station totals · equal-weight station average · requires NOAA token';
            return <label key={id} className={`block cursor-pointer rounded-xl border p-3 transition ${selectedDatasetId === id ? 'border-sky-300/35 bg-sky-300/[0.075]' : 'border-white/[0.07] bg-white/[0.02] hover:border-sky-300/20'}`}>
              <span className="flex items-start gap-3"><input type="radio" name="precipitation-dataset" value={id} checked={selectedDatasetId === id} onChange={() => setDatasetId(id)} className="mt-1 accent-sky-300" /><span><span className="block text-[12px] font-semibold text-slate-100">{title}</span><span className="mt-1 block text-[10px] leading-relaxed text-slate-400">{detail}</span></span></span>
            </label>;
          })}
        </section>;
      })()}

      {selectedVariables.length > 0 && (
        <div className="p-3 bg-hypnen-cyan/10 border border-hypnen-cyan/30 rounded-lg">
          <p className="flex items-center gap-2 text-[11px] font-medium text-sky-200">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Data selected. Continue with a region and time period.
          </p>
        </div>
      )}
    </div>
  );
}
