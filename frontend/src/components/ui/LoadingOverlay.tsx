interface LoadingOverlayProps {
  message?: string;
  progress?: number;
}

export function LoadingOverlay({ message = 'Starting the investigation…', progress = 0 }: LoadingOverlayProps) {
  const value = Math.max(0, Math.min(100, progress));
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 w-[min(380px,calc(100vw-2rem))] animate-fade-in sm:bottom-6 sm:right-6" role="status" aria-live="polite">
      <div className="pointer-events-auto overflow-hidden rounded-2xl border border-sky-200/15 bg-[#0b1421]/95 shadow-[0_18px_60px_rgba(0,0,0,0.48)] backdrop-blur-2xl">
        <div className="flex items-start gap-3.5 p-4">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-sky-200/15 bg-sky-300/[0.09]">
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-sky-100/20 border-t-sky-200" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center justify-between gap-3">
              <p className="text-[12px] font-semibold text-slate-100">Investigation in progress</p>
              <span className="shrink-0 text-[11px] font-semibold tabular-nums text-sky-200">{value}%</span>
            </div>
            <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-slate-400">{message}</p>
          </div>
        </div>
        <div className="h-1 w-full bg-white/[0.06]" role="progressbar" aria-label="Investigation progress" aria-valuemin={0} aria-valuemax={100} aria-valuenow={value}>
          <div className="h-full rounded-r-full bg-gradient-to-r from-sky-300 to-cyan-200 shadow-[0_0_12px_rgba(125,211,252,0.35)] transition-[width] duration-700" style={{ width: `${value}%` }} />
        </div>
        <div className="flex items-center justify-between px-4 py-2 text-[9px] font-medium uppercase tracking-[0.14em] text-slate-600">
          <span>Preparing your regional trend results</span>
          {value >= 78 && <span>Final analysis</span>}
        </div>
      </div>
    </div>
  );
}
