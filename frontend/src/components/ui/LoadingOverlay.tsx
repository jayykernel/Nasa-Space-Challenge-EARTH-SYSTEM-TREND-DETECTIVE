import React from 'react';

interface LoadingOverlayProps {
  message?: string;
}

export function LoadingOverlay({ message = 'Loading...' }: LoadingOverlayProps) {
  return (
    <div className="fixed inset-0 z-50 flex-center bg-hypnen-navy/90 backdrop-blur-sm animate-fade-in">
      <div className="card flex flex-col items-center gap-4 max-w-md w-full mx-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 spinner border-3" />
          <span className="text-hypnen-text font-medium">{message}</span>
        </div>
        <div className="w-full h-2 bg-hypnen-border rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-hypnen-cyan to-hypnen-blue animate-pulse" style={{ width: '100%' }} />
        </div>
        <p className="text-sm text-hypnen-text-dim text-center">
          Retrieving NASA Earth science data and performing statistical analysis...
        </p>
      </div>
    </div>
  );
}