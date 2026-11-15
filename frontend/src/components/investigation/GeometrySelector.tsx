import React, { useMemo, useState, useRef, useEffect } from 'react';
import { useStore } from '../../store/useStore';
import type { GeoJSONGeometry } from '../../types';
import indiaStatesUrl from '../../assets/india-states.geojson?url';

interface GeometrySelectorProps {
  selectedGeometry: GeoJSONGeometry | null;
}

export function GeometrySelector({ selectedGeometry }: GeometrySelectorProps) {
  const { setGeometry } = useStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectionMode, setSelectionMode] = useState<'search' | 'draw' | 'bounds' | 'admin'>('search');
  const [isSearching, setIsSearching] = useState(false);
  const [adminRegions, setAdminRegions] = useState<Array<{ properties: { name: string; iso: string }; geometry: GeoJSONGeometry }>>([]);
  const [adminQuery, setAdminQuery] = useState('');
  const [adminLoadError, setAdminLoadError] = useState('');
  const debounceRef = useRef<NodeJS.Timeout | null>(null);
  const filteredAdminRegions = useMemo(() => adminRegions.filter((feature) =>
    `${feature.properties.name} ${feature.properties.iso}`.toLowerCase().includes(adminQuery.toLowerCase())
  ), [adminRegions, adminQuery]);

  useEffect(() => {
    if (selectionMode !== 'admin' || adminRegions.length) return;
    let cancelled = false;
    fetch(indiaStatesUrl)
      .then((response) => {
        if (!response.ok) throw new Error('Could not load administrative boundaries');
        return response.json();
      })
      .then((collection) => {
        if (!cancelled) setAdminRegions(collection.features || []);
      })
      .catch((error: unknown) => {
        if (!cancelled) setAdminLoadError(error instanceof Error ? error.message : 'Could not load boundaries');
      });
    return () => { cancelled = true; };
  }, [selectionMode, adminRegions.length]);

  const handleSearch = async (query: string) => {
    if (query.length < 3) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      // Use Nominatim for geocoding
      const response = await fetch(
        `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&limit=5&polygon_geojson=1`
      );
      const data = await response.json();
      setSearchResults(data);
    } catch (err) {
      console.error('Geocoding error:', err);
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      handleSearch(searchQuery);
    }, 300);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [searchQuery]);

  const handleResultSelect = (result: any) => {
    if (result.geojson) {
      const geometry: GeoJSONGeometry = {
        type: result.geojson.type,
        coordinates: result.geojson.coordinates,
      };
      setGeometry(geometry);
      window.dispatchEvent(new CustomEvent('globe-region-name', { detail: { name: result.display_name.split(',')[0] } }));
      setSearchQuery(result.display_name);
      setSearchResults([]);
    } else if (result.boundingbox) {
      // Create bounding box polygon
      const [south, north, west, east] = result.boundingbox.map(Number);
      const geometry: GeoJSONGeometry = {
        type: 'Polygon',
        coordinates: [[
          [west, south],
          [east, south],
          [east, north],
          [west, north],
          [west, south],
        ]],
      };
      setGeometry(geometry);
      window.dispatchEvent(new CustomEvent('globe-region-name', { detail: { name: result.display_name.split(',')[0] } }));
      setSearchQuery(result.display_name);
      setSearchResults([]);
    }
  };

  const handleDrawMode = () => {
    setSelectionMode('draw');
    window.dispatchEvent(new CustomEvent('globe-bounds-mode', { detail: { enable: false } }));
    // Notify globe to enter draw mode
    window.dispatchEvent(new CustomEvent('globe-draw-mode', { detail: { enable: true } }));
  };

  const handleBoundsMode = () => {
    setSelectionMode('bounds');
    window.dispatchEvent(new CustomEvent('globe-draw-mode', { detail: { enable: false } }));
    window.dispatchEvent(new CustomEvent('globe-bounds-mode', { detail: { enable: true } }));
  };

  const activateMode = (mode: 'search' | 'draw' | 'bounds' | 'admin') => {
    setSelectionMode(mode);
    useStore.getState().setActivePanel('globe');
    if (mode === 'draw') handleDrawMode();
    else if (mode === 'bounds') handleBoundsMode();
    else {
      window.dispatchEvent(new CustomEvent('globe-draw-mode', { detail: { enable: false } }));
      window.dispatchEvent(new CustomEvent('globe-bounds-mode', { detail: { enable: false } }));
      if (mode === 'admin') handleAdminMode();
    }
  };

  const handleAdminMode = () => {
    setSelectionMode('admin');
  };

  const handleClearGeometry = () => {
    setGeometry(null);
    window.dispatchEvent(new CustomEvent('globe-clear-selection'));
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div><p className="text-[10px] font-semibold uppercase tracking-[0.17em] text-sky-300/70">Step 2</p><h3 className="mt-1 text-[16px] font-semibold tracking-tight text-slate-100">Choose a region</h3></div>
        {selectedGeometry && (
          <button
            onClick={handleClearGeometry}
            className="text-xs text-hypnen-text-dim hover:text-hypnen-red transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Selection Mode Tabs */}
      <div className="grid grid-cols-4 gap-1 rounded-xl border border-white/[0.07] bg-black/15 p-1">
        {[
          { id: 'search', label: 'Search' },
          { id: 'draw', label: 'Draw' },
          { id: 'bounds', label: 'Box' },
          { id: 'admin', label: 'States' },
        ].map((mode) => (
          <button
            key={mode.id}
            onClick={() => activateMode(mode.id as 'search' | 'draw' | 'bounds' | 'admin')}
            className={`flex items-center justify-center rounded-lg px-1.5 py-2 text-[10px] font-medium transition-all ${
              selectionMode === mode.id
                ? 'bg-sky-300/15 text-sky-100 shadow-sm'
                : 'text-slate-500 hover:bg-white/[0.04] hover:text-slate-200'
            }`}
          >
            <span>{mode.label}</span>
          </button>
        ))}
      </div>

      {/* Search Mode */}
      {selectionMode === 'search' && (
        <div className="space-y-4">
          <div className="relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search a place, region, or country"
              className="w-full rounded-xl border border-white/[0.09] bg-white/[0.03] px-3.5 py-3 text-[12px] text-slate-100 placeholder:text-slate-500 focus:border-sky-300/40 focus:outline-none focus:ring-2 focus:ring-sky-300/10"
            />
            {isSearching && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <div className="w-4 h-4 spinner border-2 border-hypnen-border border-t-hypnen-cyan" />
              </div>
            )}
          </div>

          {searchResults.length > 0 && (
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {searchResults.map((result, idx) => (
                <button
                  key={idx}
                  onClick={() => handleResultSelect(result)}
                  className="w-full p-3 rounded-lg border border-hypnen-border bg-hypnen-card hover:border-hypnen-cyan/30 hover:bg-hypnen-cyan/10 transition-all text-left"
                >
                  <div className="font-medium text-hypnen-text text-sm">{result.display_name.split(',')[0]}</div>
                  <div className="text-xs text-hypnen-text-dim mt-1 truncate">{result.display_name}</div>
                  <div className="flex items-center gap-2 mt-2 text-xs text-hypnen-text-dim">
                    <span className="flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      {result.geojson ? 'Polygon' : 'Bounding Box'}
                    </span>
                    <span className="flex items-center gap-1">
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                      </svg>
                      {result.class || 'Location'}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Draw Mode */}
      {selectionMode === 'draw' && (
        <div className="space-y-4 p-4 bg-hypnen-cyan/10 border border-hypnen-cyan/30 rounded-lg">
          <div className="flex items-center gap-2 text-hypnen-cyan">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            <span className="font-medium">Draw Mode Active</span>
          </div>
          <p className="text-sm text-hypnen-text">
            Click on the globe to add vertices. Double-click or click the first point to close the polygon.
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => window.dispatchEvent(new CustomEvent('globe-undo-last-point'))}
              className="px-3 py-1.5 text-sm bg-hypnen-card border border-hypnen-border rounded-lg hover:border-hypnen-cyan/30 transition-colors"
            >
              Undo Last Point
            </button>
            <button
              onClick={() => window.dispatchEvent(new CustomEvent('globe-clear-drawing'))}
              className="px-3 py-1.5 text-sm bg-hypnen-card border border-hypnen-border rounded-lg hover:border-hypnen-red/30 text-hypnen-red transition-colors"
            >
              Clear Drawing
            </button>
          </div>
        </div>
      )}

      {/* Bounds Mode */}
      {selectionMode === 'bounds' && (
        <div className="space-y-4 p-4 bg-hypnen-blue/10 border border-hypnen-blue/30 rounded-lg">
          <div className="flex items-center gap-2 text-hypnen-blue">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 16h18M3 8h18m0 0V4a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2h14a2 2 0 002-2V8" />
            </svg>
            <span className="font-medium">Rectangle Selection</span>
          </div>
          <p className="text-sm text-hypnen-text">
            Click and drag on the globe to draw a rectangular region.
          </p>
        </div>
      )}

      {/* Admin Mode */}
      {selectionMode === 'admin' && (
        <div className="space-y-4 p-4 bg-hypnen-teal/10 border border-hypnen-teal/30 rounded-lg">
          <div className="flex items-center gap-2 text-hypnen-teal">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
            <span className="font-medium">Administrative Boundaries</span>
          </div>
          <p className="text-sm text-hypnen-text">Choose an India state or union territory. Use Search or Draw for other regions.</p>
          <input value={adminQuery} onChange={(event) => setAdminQuery(event.target.value)} placeholder="Filter states and territories" aria-label="Filter administrative boundaries" className="w-full rounded-lg border border-hypnen-border bg-hypnen-card px-3 py-2 text-sm text-hypnen-text placeholder-hypnen-text-dim" />
          {adminLoadError && <p role="alert" className="text-xs text-hypnen-red">{adminLoadError}</p>}
          <div className="max-h-64 space-y-1 overflow-y-auto pr-1">
            {filteredAdminRegions.map((feature) => (
              <button key={feature.properties.iso} onClick={() => {
                setGeometry(feature.geometry);
                window.dispatchEvent(new CustomEvent('globe-region-name', { detail: { name: feature.properties.name } }));
                setSearchQuery(`${feature.properties.name}, India`);
              }} className="flex w-full items-center justify-between rounded-lg border border-transparent px-3 py-2 text-left text-sm text-hypnen-text transition hover:border-hypnen-teal/30 hover:bg-hypnen-card">
                <span>{feature.properties.name}</span><span className="font-mono text-xs text-hypnen-text-dim">{feature.properties.iso}</span>
              </button>
            ))}
            {!adminLoadError && !filteredAdminRegions.length && <p className="px-3 py-2 text-xs text-hypnen-text-dim">Loading available boundaries…</p>}
          </div>
          <p className="text-xs text-hypnen-text-dim">geoBoundaries gbOpen · CC BY 4.0</p>
        </div>
      )}

      {/* Current Selection Info */}
      {selectedGeometry && (
        <div className="card border-hypnen-cyan/30 bg-hypnen-cyan/5">
          <h4 className="text-sm font-medium text-hypnen-cyan mb-3 flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Selected Region
          </h4>
          <div className="rounded-lg bg-hypnen-navy p-3 text-xs text-hypnen-text-dim">
            <div className="flex justify-between"><span>Geometry</span><span className="font-mono text-hypnen-text">{selectedGeometry.type}</span></div>
            <div className="mt-2 flex justify-between"><span>Boundary points</span><span className="font-mono text-hypnen-text">{countVertices(selectedGeometry.coordinates)}</span></div>
            <div className="mt-2 truncate"><span>Approximate extent: </span><span className="font-mono">{formatBounds(selectedGeometry.coordinates)}</span></div>
          </div>
          <div className="mt-2 flex gap-2">
            <button
              onClick={() => {
                navigator.clipboard.writeText(JSON.stringify(selectedGeometry));
              }}
              className="text-xs px-3 py-1.5 bg-hypnen-card border border-hypnen-border rounded-lg hover:border-hypnen-cyan/30 transition-colors"
            >
              Copy GeoJSON
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function countVertices(value: unknown): number {
  if (!Array.isArray(value)) return 0;
  if (value.length >= 2 && value.every((part) => typeof part === 'number')) return 1;
  return value.reduce<number>((total, item) => total + countVertices(item), 0);
}

function formatBounds(coordinates: unknown): string {
  const points: number[][] = [];
  const collect = (value: unknown) => {
    if (!Array.isArray(value)) return;
    if (value.length >= 2 && typeof value[0] === 'number' && typeof value[1] === 'number') points.push(value as number[]);
    else value.forEach(collect);
  };
  collect(coordinates);
  if (!points.length) return 'Unavailable';
  const longitudes = points.map(([longitude]) => longitude);
  const latitudes = points.map(([, latitude]) => latitude);
  return `${Math.min(...longitudes).toFixed(2)}°–${Math.max(...longitudes).toFixed(2)}°, ${Math.min(...latitudes).toFixed(2)}°–${Math.max(...latitudes).toFixed(2)}°`;
}
