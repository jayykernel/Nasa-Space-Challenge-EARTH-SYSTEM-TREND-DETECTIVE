import { useState } from 'react';
import { useStore } from '../../store/useStore';
import { VariableSelector } from './VariableSelector';
import { GeometrySelector } from './GeometrySelector';
import { TimeRangeSelector } from './TimeRangeSelector';
import { RunAnalysisButton } from './RunAnalysisButton';

const sections = [
  { id: 'variables', label: 'Data', number: '01', hint: 'Source' },
  { id: 'geometry', label: 'Region', number: '02', hint: 'Place' },
  { id: 'time', label: 'Period', number: '03', hint: 'Dates' },
  { id: 'run', label: 'Analyze', number: '04', hint: 'Review' },
] as const;

export function InvestigationSidebar() {
  const { investigation, data } = useStore();
  const [activeSection, setActiveSection] = useState<string>('variables');
  const readyCount = Number(investigation.variables.length > 0) + Number(Boolean(investigation.geometry)) + Number(Boolean(investigation.timeRange.start && investigation.timeRange.end));

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden bg-[#0a111d]">
      <div className="shrink-0 border-b border-white/[0.07] px-4 pb-4 pt-5 sm:px-5">
        <div className="mb-4 flex items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.19em] text-sky-300/75">Investigation setup</p>
            <h2 className="mt-1 text-[17px] font-semibold tracking-tight text-slate-100">Build your study</h2>
          </div>
          <span className="mt-1 rounded-full border border-white/[0.08] bg-white/[0.035] px-2.5 py-1 text-[10px] font-medium tabular-nums text-slate-400">{readyCount} of 3 ready</span>
        </div>
        <nav aria-label="Investigation steps" className="grid grid-cols-4 gap-1">
          {sections.map((section, index) => {
            const active = activeSection === section.id;
            const complete = (section.id === 'variables' && investigation.variables.length > 0) || (section.id === 'geometry' && Boolean(investigation.geometry)) || (section.id === 'time' && Boolean(investigation.timeRange.start && investigation.timeRange.end));
            return (
              <button
                key={section.id}
                type="button"
                onClick={() => setActiveSection(section.id)}
                aria-current={active ? 'step' : undefined}
                className={`group relative flex min-w-0 flex-col items-center gap-1.5 rounded-xl px-1 py-2 transition ${active ? 'bg-sky-300/[0.09]' : 'hover:bg-white/[0.035]'}`}
              >
                {index < sections.length - 1 && <span className="absolute right-[-7px] top-[18px] h-px w-3 bg-white/10" />}
                <span className={`flex h-7 w-7 items-center justify-center rounded-lg border text-[10px] font-semibold tabular-nums transition ${active ? 'border-sky-200/30 bg-sky-300/15 text-sky-100' : complete ? 'border-emerald-300/20 bg-emerald-300/[0.08] text-emerald-300' : 'border-white/[0.08] bg-white/[0.025] text-slate-500 group-hover:text-slate-300'}`}>
                  {complete && !active ? '✓' : section.number}
                </span>
                <span className={`text-[10px] font-medium ${active ? 'text-slate-100' : 'text-slate-500 group-hover:text-slate-300'}`}>{section.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-5">
        {activeSection === 'variables' && <VariableSelector availableVariables={data.variables} selectedVariables={investigation.variables} selectedDatasetId={investigation.datasetId} />}
        {activeSection === 'geometry' && <GeometrySelector selectedGeometry={investigation.geometry} />}
        {activeSection === 'time' && <TimeRangeSelector timeRange={investigation.timeRange} temporalResolution={investigation.temporalResolution} datasetId={investigation.datasetId} />}
        {activeSection === 'run' && <RunAnalysisButton />}
      </div>

      <div className="shrink-0 border-t border-white/[0.07] bg-black/10 px-4 py-3 sm:px-5">
        <div className="mb-2 flex items-center justify-between">
          <span className="text-[10px] font-semibold uppercase tracking-[0.15em] text-slate-500">Study summary</span>
          <span className="h-1.5 w-1.5 rounded-full bg-sky-300/80" />
        </div>
        <div className="grid grid-cols-[1fr_auto] gap-x-3 gap-y-1.5 text-[11px]">
          <span className="text-slate-500">Region</span><span className="max-w-[180px] truncate text-right text-slate-300">{investigation.geometry ? 'Selected' : 'Choose a region'}</span>
          <span className="text-slate-500">Period</span><span className="text-right tabular-nums text-slate-300">{investigation.timeRange.start.slice(0, 4)} — {investigation.timeRange.end.slice(0, 4)}</span>
          <span className="text-slate-500">Resolution</span><span className="text-right capitalize text-slate-300">{investigation.temporalResolution}</span>
        </div>
      </div>
    </div>
  );
}
