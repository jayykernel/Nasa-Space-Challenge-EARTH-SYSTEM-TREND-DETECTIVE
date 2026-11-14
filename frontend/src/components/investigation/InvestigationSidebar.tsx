import React, { useState } from 'react';
import { useStore } from '../../store/useStore';
import { VariableSelector } from './VariableSelector';
import { GeometrySelector } from './GeometrySelector';
import { TimeRangeSelector } from './TimeRangeSelector';
import { RunAnalysisButton } from './RunAnalysisButton';

export function InvestigationSidebar() {
  const { investigation, ui, data } = useStore();
  const [activeSection, setActiveSection] = useState<string>('variables');

  const sections = [
    { id: 'variables', label: 'Variables', icon: '📊' },
    { id: 'geometry', label: 'Region', icon: '🌍' },
    { id: 'time', label: 'Time Range', icon: '📅' },
    { id: 'run', label: 'Run Analysis', icon: '🚀' },
  ];

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Section Navigation */}
      <div className="p-4 border-b border-hypnen-border">
        <div className="flex gap-1 overflow-x-auto pb-2">
          {sections.map((section) => (
            <button
              key={section.id}
              onClick={() => setActiveSection(section.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                activeSection === section.id
                  ? 'bg-hypnen-cyan/20 text-hypnen-cyan border border-hypnen-cyan/30'
                  : 'text-hypnen-text-dim hover:text-hypnen-text hover:bg-hypnen-card'
              }`}
            >
              <span>{section.icon}</span>
              <span>{section.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Section Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {activeSection === 'variables' && (
          <VariableSelector
            availableVariables={data.variables}
            selectedVariables={investigation.variables}
          />
        )}

        {activeSection === 'geometry' && (
          <GeometrySelector selectedGeometry={investigation.geometry} />
        )}

        {activeSection === 'time' && (
          <TimeRangeSelector
            timeRange={investigation.timeRange}
            temporalResolution={investigation.temporalResolution}
          />
        )}

        {activeSection === 'run' && <RunAnalysisButton />}
      </div>

      {/* Status Bar */}
      <div className="p-4 border-t border-hypnen-border bg-hypnen-navy/50">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-hypnen-text-dim">Variables</span>
            <span className="text-hypnen-text font-mono">{investigation.variables.length}</span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-hypnen-text-dim">Region</span>
            <span className="text-hypnen-text font-mono">
              {investigation.geometry ? 'Selected' : 'Not selected'}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-hypnen-text-dim">Time Range</span>
            <span className="text-hypnen-text font-mono">
              {investigation.timeRange.start} → {investigation.timeRange.end}
            </span>
          </div>
          <div className="flex items-center justify-between text-xs">
            <span className="text-hypnen-text-dim">Resolution</span>
            <span className="text-hypnen-text font-mono capitalize">{investigation.temporalResolution}</span>
          </div>
        </div>
      </div>
    </div>
  );
}