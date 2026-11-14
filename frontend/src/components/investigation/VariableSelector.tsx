import React from 'react';
import { useStore } from '../../store/useStore';
import type { VariableInfo } from '../../types';

interface VariableSelectorProps {
  availableVariables: VariableInfo[];
  selectedVariables: string[];
}

export function VariableSelector({ availableVariables, selectedVariables }: VariableSelectorProps) {
  const { setVariables } = useStore();

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
    const newSelection = selectedVariables.includes(key)
      ? selectedVariables.filter(v => v !== key)
      : [...selectedVariables, key];
    setVariables(newSelection);
  };

  const VariableGroup = ({ title, variables }: { title: string; variables: VariableInfo[] }) => (
    <div className="space-y-3">
      <h4 className="text-xs font-semibold text-hypnen-text-dim uppercase tracking-wider">{title}</h4>
      {variables.map((variable) => (
        <button
          key={variable.key}
          onClick={() => toggleVariable(variable.key)}
          className={`w-full p-3 rounded-lg border transition-all text-left ${
            selectedVariables.includes(variable.key)
              ? 'bg-hypnen-cyan/10 border-hypnen-cyan/50'
              : 'border-hypnen-border hover:border-hypnen-cyan/30 hover:bg-hypnen-card'
          }`}
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-hypnen-text">{variable.display_name}</span>
                {selectedVariables.includes(variable.key) && (
                  <span className="w-2 h-2 rounded-full bg-hypnen-cyan" />
                )}
              </div>
              <p className="text-xs text-hypnen-text-dim mt-1 line-clamp-2">{variable.description}</p>
              <div className="flex items-center gap-3 mt-2 text-xs text-hypnen-text-dim">
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
            <div className="w-6 h-6 rounded border-2 flex items-center justify-center flex-shrink-0 ${
              selectedVariables.includes(variable.key)
                ? 'bg-hypnen-cyan border-hypnen-cyan'
                : 'border-hypnen-border text-hypnen-text-dim'
            }">
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
        <h3 className="text-lg font-semibold text-hypnen-text">Environmental Variables</h3>
        <span className="text-sm text-hypnen-text-dim">
          {selectedVariables.length} selected
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

      {selectedVariables.length > 0 && (
        <div className="p-3 bg-hypnen-cyan/10 border border-hypnen-cyan/30 rounded-lg">
          <p className="text-sm text-hypnen-cyan font-medium flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            {selectedVariables.length} variable{selectedVariables.length !== 1 ? 's' : ''} selected. Ready to investigate.
          </p>
        </div>
      )}
    </div>
  );
}