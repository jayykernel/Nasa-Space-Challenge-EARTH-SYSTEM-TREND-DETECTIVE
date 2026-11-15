interface HeaderProps {
  onToggleSidebar: () => void;
  sidebarOpen: boolean;
  backendConnected: boolean;
  activePanel: 'globe' | 'map' | 'results';
  onPanelChange: (panel: 'globe' | 'map' | 'results') => void;
  hasResults: boolean;
}

const views = [
  { id: 'globe', label: 'Globe' },
  { id: 'map', label: 'Map' },
  { id: 'results', label: 'Results' },
] as const;

export function Header({ onToggleSidebar, sidebarOpen, backendConnected, activePanel, onPanelChange, hasResults }: HeaderProps) {
  return (
    <header className="relative z-30 flex h-[68px] shrink-0 items-center justify-between gap-3 border-b border-white/[0.08] bg-[#080e19]/95 px-3 shadow-[0_8px_32px_rgba(0,0,0,0.16)] backdrop-blur-xl sm:px-5 lg:px-7">
      <div className="flex min-w-0 items-center gap-3 sm:gap-4">
        <button
          onClick={onToggleSidebar}
          className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/[0.08] bg-white/[0.035] text-slate-300 transition hover:border-sky-300/25 hover:bg-sky-300/10 hover:text-white"
          aria-label={sidebarOpen ? 'Close investigation controls' : 'Open investigation controls'}
        >
          <svg className="h-[18px] w-[18px]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div className="flex min-w-0 items-center gap-3">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-sky-300/25 bg-gradient-to-br from-sky-300/25 to-blue-500/20 text-sky-200 shadow-[0_0_24px_rgba(56,189,248,0.12)]">
            <svg className="h-[21px] w-[21px]" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="9" strokeWidth="1.5" />
              <path strokeLinecap="round" strokeWidth="1.5" d="M3 12h18M12 3a14 14 0 010 18m0-18a14 14 0 000 18M5.6 6.5h12.8M5.6 17.5h12.8" />
            </svg>
          </div>
          <div className="min-w-0">
            <h1 className="truncate text-[13px] font-semibold tracking-[0.015em] text-slate-100 sm:text-[15px]">Earth System Trend Detective</h1>
            <p className="hidden text-[10px] font-medium uppercase tracking-[0.16em] text-slate-500 sm:block">Earth observation workspace</p>
          </div>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2 sm:gap-4">
        <nav aria-label="Workspace view" className="flex items-center gap-0.5 rounded-xl border border-white/[0.08] bg-black/20 p-1">
          {views.map(({ id, label }) => {
            const active = activePanel === id;
            return (
              <button
                key={id}
                type="button"
                onClick={() => onPanelChange(id)}
                disabled={id === 'results' && !hasResults}
                aria-current={active ? 'page' : undefined}
                className={`rounded-lg px-2.5 py-1.5 text-[11px] font-medium transition sm:px-3.5 sm:text-xs ${active ? 'bg-sky-300/15 text-sky-100 ring-1 ring-inset ring-sky-200/15 shadow-sm' : 'text-slate-400 hover:bg-white/[0.05] hover:text-slate-100'} disabled:cursor-not-allowed disabled:opacity-35`}
              >
                {label}
              </button>
            );
          })}
        </nav>

        <div className="hidden h-7 w-px bg-white/10 sm:block" />
        <div className="flex items-center gap-2 rounded-full border border-white/[0.07] bg-white/[0.025] px-2.5 py-1.5" title={backendConnected ? 'Backend API is available' : 'Analysis API is unavailable'}>
          <span className={`h-1.5 w-1.5 rounded-full ${backendConnected ? 'bg-emerald-400 shadow-[0_0_9px_rgba(52,211,153,0.7)]' : 'bg-amber-400'}`} />
          <span className="hidden text-[10px] font-medium text-slate-400 md:inline">{backendConnected ? 'Connected' : 'Offline'}</span>
        </div>
      </div>
    </header>
  );
}
