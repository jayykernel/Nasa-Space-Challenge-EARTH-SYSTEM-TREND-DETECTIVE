import { useEffect } from 'react';
import { GeoJSON, MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import type { GeoJsonObject } from 'geojson';
import { useStore } from '../../store/useStore';
import type { GeoJSONGeometry } from '../../types';
import 'leaflet/dist/leaflet.css';

interface MapViewProps {
  onGeometrySelect?: (geometry: GeoJSONGeometry) => void;
}

function MapControls() {
  const map = useMap();
  return <div className="absolute right-4 top-20 z-[1000] flex flex-col gap-2">
    <button onClick={() => map.flyTo([20, 0], 2, { duration: 1 })} className="card rounded-lg p-2 text-hypnen-text" title="Reset view">⌂</button>
  </div>;
}

function CoordinateReadout() {
  useMapEvents({ mousemove(event) {
    const output=document.getElementById('map-coords');
    if (output) output.textContent=`Lon ${event.latlng.lng.toFixed(3)}° · Lat ${event.latlng.lat.toFixed(3)}°`;
  }});
  return <div id="map-coords" className="absolute bottom-4 left-4 z-[1000] rounded-lg border border-hypnen-border bg-hypnen-navy/90 px-3 py-2 text-xs text-hypnen-text-dim">Lon 0.000° · Lat 0.000°</div>;
}

function SpatialTrendLayer() {
  const { data } = useStore();
  const results=data.currentInvestigation?.spatial_results;
  const cells=results ? Object.values(results)[0] as any[] : [];
  if (!cells?.length) return null;
  const half=.05;
  const geojson={
    type:'FeatureCollection' as const,
    features:cells.map((cell:any)=>({type:'Feature' as const,geometry:{type:'Polygon' as const,coordinates:[[
      [cell.lon-half,cell.lat-half],[cell.lon+half,cell.lat-half],[cell.lon+half,cell.lat+half],[cell.lon-half,cell.lat+half],[cell.lon-half,cell.lat-half],
    ]]},properties:{trend_direction:cell.trend_direction,trend_magnitude:cell.trend_magnitude,p_value:cell.p_value,significance:cell.significance}})),
  };
  return <GeoJSON data={geojson as GeoJsonObject} style={(feature:any)=>{
    const direction=feature?.properties?.trend_direction;
    const color=direction==='increasing'?'#00b894':direction==='decreasing'?'#e74c3c':'#8b949e';
    return {color,weight:1,fillColor:color,fillOpacity:feature?.properties?.significance ? .5 : .22};
  }} onEachFeature={(feature:any,layer:any)=>{
    const props=feature.properties;
    const slope=typeof props.trend_magnitude==='number'?props.trend_magnitude.toExponential(3):'N/A';
    const p=typeof props.p_value==='number'?props.p_value.toPrecision(3):'N/A';
    layer.bindPopup(`Trend: ${props.trend_direction}<br>Sen slope: ${slope}<br>Mann–Kendall p: ${p}`);
  }} />;
}

export function MapView({ onGeometrySelect }: MapViewProps) {
  const { investigation, setActivePanel }=useStore();
  useEffect(()=>{ if (investigation.geometry) window.setTimeout(()=>window.dispatchEvent(new Event('resize')),50); },[investigation.geometry]);
  return <div className="relative h-full w-full">
    <div className="absolute left-4 top-4 z-[1000] inline-flex items-center rounded-xl border border-white/10 bg-[#081323]/90 p-1 shadow-xl backdrop-blur-xl">
      <button onClick={()=>setActivePanel('globe')} className="rounded-lg px-4 py-2 text-sm font-medium text-slate-300 transition hover:text-white">◎ 3D Globe</button>
      <button onClick={()=>setActivePanel('map')} className="rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950">▧ 2D Map</button>
    </div>
    <MapContainer center={[20,0]} zoom={2} className="h-full w-full" maxZoom={19} minZoom={1} zoomControl attributionControl>
      <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" maxZoom={19} />
      {investigation.geometry && <GeoJSON data={investigation.geometry as unknown as GeoJsonObject} style={{color:'#00d4ff',weight:3,fillColor:'#00d4ff',fillOpacity:.22,dashArray:'7, 4'}} eventHandlers={{click:()=>onGeometrySelect?.(investigation.geometry!)}} />}
      <SpatialTrendLayer />
      <MapControls />
      <CoordinateReadout />
    </MapContainer>
  </div>;
}
