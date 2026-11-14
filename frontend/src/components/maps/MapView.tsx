import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, GeoJSON, Polygon, Rectangle, LayerGroup, useMapEvents, Map } from 'react-leaflet';
import L, { LatLngBounds, GeoJSON as LGeoJSON, Layer } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useStore } from '../../store/useStore';
import type { GeoJSONGeometry } from '../../types';

// Fix Leaflet default icon issue
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface MapViewProps {
  onGeometrySelect?: (geometry: GeoJSONGeometry) => void;
}

const DarkTileLayer = () => (
  <TileLayer
    attribution='&copy; <a href="https://stadiamaps.com/">Stadia Maps</a> &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="https://openstreetmap.org">OpenStreetMap</a> contributors'
    url="https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png"
    maxZoom={19}
    subdomains="abcd"
  />
);

const CountryBoundaries = () => {
  const [geoJson, setGeoJson] = useState<any>(null);

  useEffect(() => {
    fetch('https://unpkg.com/world-atlas@2.0.2/countries-110m.json')
      .then(res => res.json())
      .then(data => {
        // Convert TopoJSON to GeoJSON
        // For simplicity, we'll use a pre-converted version or skip
        setGeoJson(data);
      })
      .catch(err => console.warn('Could not load country boundaries:', err));
  }, []);

  if (!geoJson) return null;

  // Note: This is TopoJSON, would need topojson-client to convert
  // For now, return null and we'll add a simpler boundary layer
  return null;
};

const SelectedRegionLayer = ({ geometry, onSelect }: { geometry: GeoJSONGeometry | null; onSelect?: (geometry: GeoJSONGeometry) => void }) => {
  const [selectedLayer, setSelectedLayer] = useState<any>(null);

  useEffect(() => {
    if (!geometry) return;

    const layer = L.geoJSON(geometry, {
      style: {
        color: '#00d4ff',
        weight: 3,
        fillColor: '#00d4ff',
        fillOpacity: 0.3,
        dashArray: '8, 4',
      },
      onEachFeature: (feature, layer) => {
        layer.on('click', () => onSelect?.(geometry));
      },
    });

    setSelectedLayer(layer);
    return () => setSelectedLayer(null);
  }, [geometry, onSelect]);

  return selectedLayer ? <LayerGroup>{selectedLayer}</LayerGroup> : null;
};

const DrawControl = ({ onDrawComplete }: { onDrawComplete: (geometry: GeoJSONGeometry) => void }) => {
  const map = useMapEvents({
    click(e) {
      // Custom draw logic would go here
    },
  });

  useEffect(() => {
    // Add Leaflet.draw control if needed
    // For now, we'll use a simpler approach
  }, [map]);

  return null;
};

const CoordinateDisplay = () => {
  const map = useMapEvents({
    mousemove(e) {
      const coords = document.getElementById('map-coords');
      if (coords) {
        coords.textContent = `Lon: ${e.latlng.lng.toFixed(3)}°, Lat: ${e.latlng.lat.toFixed(3)}°`;
      }
    },
  });

  return (
    <div id="map-coords" className="fixed bottom-4 left-4 z-20 bg-hypnen-navy/90 backdrop-blur-sm border border-hypnen-border rounded-lg px-3 py-2 text-xs font-mono text-hypnen-text-dim pointer-events-none" style={{ fontFamily: 'JetBrains Mono, monospace' }}>
      Lon: 0.000°, Lat: 0.000°
    </div>
  );
};

const ViewControls = () => {
  const map = useMapEvents({});

  return (
    <div className="fixed top-20 right-4 z-20 flex flex-col gap-2">
      <button
        onClick={() => map.flyTo([20, 0], 2, { duration: 2 })}
        className="card p-2 rounded-lg hover:bg-hypnen-cyan/10 hover:border-hypnen-cyan/30 transition-all"
        title="Reset View"
      >
        <svg className="w-5 h-5 text-hypnen-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
      <button
        onClick={() => map.invalidateSize()}
        className="card p-2 rounded-lg hover:bg-hypnen-cyan/10 hover:border-hypnen-cyan/30 transition-all"
        title="Refresh Map"
      >
        <svg className="w-5 h-5 text-hypnen-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      </button>
    </div>
  );
};

const Legend = () => (
  <div className="fixed bottom-4 right-4 z-20 card p-3 min-w-[180px]">
    <div className="text-xs font-medium text-hypnen-text mb-2">Map Layers</div>
    <div className="space-y-2 text-xs">
      <div className="flex items-center gap-2 text-hypnen-text-dim">
        <div className="w-4 h-4 rounded border border-hypnen-border/50 bg-hypnen-card" />
        <span>Base Map</span>
      </div>
      <div className="flex items-center gap-2 text-hypnen-cyan">
        <div className="w-4 h-4 rounded bg-hypnen-cyan/40 border border-hypnen-cyan" />
        <span>Selected Region</span>
      </div>
      <div className="flex items-center gap-2 text-hypnen-teal">
        <div className="w-4 h-4 rounded bg-hypnen-teal/40 border border-hypnen-teal" />
        <span>Trend: Increasing</span>
      </div>
      <div className="flex items-center gap-2 text-hypnen-red">
        <div className="w-4 h-4 rounded bg-hypnen-red/40 border border-hypnen-red" />
        <span>Trend: Decreasing</span>
      </div>
      <div className="flex items-center gap-2 text-hypnen-yellow">
        <div className="w-4 h-4 rounded bg-hypnen-yellow/40 border border-hypnen-yellow" />
        <span>Trend: Not Significant</span>
      </div>
      <div className="flex items-center gap-2 text-hypnen-text-dim">
        <div className="w-4 h-4 rounded bg-gray-500/40 border border-gray-500" />
        <span>Insufficient Data</span>
      </div>
    </div>
  </div>
);

const SpatialTrendLayer = () => {
  const { data } = useStore();
  const [trendLayer, setTrendLayer] = useState<Layer | null>(null);

  useEffect(() => {
    const spatialResults = data.currentInvestigation?.spatial_results;
    if (!spatialResults) {
      setTrendLayer(null);
      return;
    }

    // Get first variable's spatial results
    const firstVar = Object.keys(spatialResults)[0];
    if (!firstVar) {
      setTrendLayer(null);
      return;
    }

    const cells = spatialResults[firstVar];
    if (!cells || cells.length === 0) {
      setTrendLayer(null);
      return;
    }

    // Create GeoJSON for trend cells
    const features = cells.map((cell: any) => {
      const cellSize = 0.25; // approximate grid cell size in degrees
      const halfSize = cellSize / 2;
      return {
        type: 'Feature',
        geometry: {
          type: 'Polygon',
          coordinates: [[
            [cell.lon - halfSize, cell.lat - halfSize],
            [cell.lon + halfSize, cell.lat - halfSize],
            [cell.lon + halfSize, cell.lat + halfSize],
            [cell.lon - halfSize, cell.lat + halfSize],
            [cell.lon - halfSize, cell.lat - halfSize],
          ]],
        },
        properties: {
          trend_direction: cell.trend_direction,
          trend_magnitude: cell.trend_magnitude,
          p_value: cell.p_value,
          significance: cell.significance,
        },
      };
    });

    const geojson = {
      type: 'FeatureCollection',
      features,
    };

    const layer = L.geoJSON(geojson, {
      style: (feature: any) => {
        const trend = feature.properties.trend_direction;
        const sig = feature.properties.significance;
        let color = '#8b949e'; // default gray
        let opacity = 0.3;

        if (trend === 'increasing' && sig) {
          color = '#00b894'; // teal
          opacity = 0.6;
        } else if (trend === 'decreasing' && sig) {
          color = '#e74c3c'; // red
          opacity = 0.6;
        } else if (trend === 'no_significant_trend') {
          color = '#f39c12'; // yellow
          opacity = 0.4;
        } else if (trend === 'insufficient_data') {
          color = '#8b949e'; // gray
          opacity = 0.2;
        }

        return {
          color: color,
          weight: 1,
          fillColor: color,
          fillOpacity: opacity,
        };
      },
      onEachFeature: (feature: any, layer: any) => {
        const props = feature.properties;
        layer.bindPopup(`
          <div class="p-2 min-w-[200px]">
            <h4 class="font-medium text-hypnen-text mb-1">Grid Cell Trend</h4>
            <div class="text-xs text-hypnen-text-dim space-y-1">
              <div><strong>Direction:</strong> {props.trend_direction.replace('_', ' ')}</div>
              <div><strong>Magnitude:</strong> {props.trend_magnitude?.toFixed(4) || 'N/A'} units/year</div>
              <div><strong>P-value:</strong> {props.p_value?.toFixed(4) || 'N/A'}</div>
              <div><strong>Significant:</strong> {props.significance ? 'Yes' : 'No'}</div>
            </div>
          </div>
        `);
      },
    });

    setTrendLayer(layer);
    return () => setTrendLayer(null);
  }, [data.currentInvestigation?.spatial_results]);

  return trendLayer ? <LayerGroup>{trendLayer}</LayerGroup> : null;
};

export function MapView({ onGeometrySelect }: MapViewProps) {
  const { investigation, ui } = useStore();
  const mapRef = useRef<Map | null>(null);

  const handleMapClick = (e: any) => {
    // Could implement click-to-add-point for polygon drawing here
  };

  return (
    <div className="relative h-full w-full">
      <MapContainer
        ref={mapRef}
        center={[20, 0]}
        zoom={2}
        className="h-full w-full"
        maxZoom={19}
        minZoom={1}
        zoomControl={false}
        attributionControl={false}
      >
        <DarkTileLayer />
        <CoordinateDisplay />
        <SelectedRegionLayer geometry={investigation.geometry} onSelect={onGeometrySelect} />
        <SpatialTrendLayer />
        <ViewControls />
        <Legend />
      </MapContainer>

      {/* Map Mode Indicator */}
      <div className="fixed top-20 left-4 right-4 z-30">
        <div className="max-w-md mx-auto card border-hypnen-teal/50 bg-hypnen-teal/10 p-3 flex items-center gap-3">
          <svg className="w-5 h-5 text-hypnen-teal flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          <span className="text-sm font-medium text-hypnen-text">2D Scientific Map View</span>
          <span className="ml-auto text-xs text-hypnen-text-dim px-2 py-1 bg-hypnen-card rounded border border-hypnen-border">
            Leaflet
          </span>
        </div>
      </div>
    </div>
  );
}