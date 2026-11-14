import React from 'react';

interface HeaderProps {
  onToggleSidebar: () => void;
  sidebarOpen: boolean;
}

export function Header({ onToggleSidebar, sidebarOpen }: HeaderProps) {
  return (
    <header className="h-14 border-b border-hypnen-border bg-hypnen-navy/90 backdrop-blur-sm flex items-center justify-between px-4 z-20">
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg hover:bg-hypnen-card transition-colors text-hypnen-text-dim hover:text-hypnen-text"
          aria-label={sidebarOpen ? 'Close sidebar' : 'Open sidebar'}
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-hypnen-cyan to-hypnen-blue flex items-center justify-center">
            <svg className="w-5 h-5 text-hypnen-navy" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
            </svg>
          </div>
          <div>
            <h1 className="text-lg font-semibold text-hypnen-text">Earth System Trend Detective</h1>
            <p className="text-xs text-hypnen-text-dim">Explore Earth. Detect Change. Understand Our Planet.</p>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* NASA Badge */}
        <span className="px-3 py-1 text-xs font-medium bg-hypnen-blue/20 text-hypnen-blue rounded-full border border-hypnen-blue/30">
          NASA Space Apps 2026
        </span>

        {/* Status indicator */}
        <div className="flex items-center gap-2 text-sm text-hypnen-text-dim">
          <span className="w-2 h-2 rounded-full bg-hypnen-green animate-pulse" />
          <span>Backend Connected</span>
        </div>
      </div>
    </header>
  );
}