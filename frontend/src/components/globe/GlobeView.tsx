import { useEffect, useRef, useState } from 'react';
import { Viewer, Entity, Cartesian3, Color, PolygonHierarchy, Rectangle, ScreenSpaceEventHandler, ScreenSpaceEventType, defined, Math as CesiumMath, GeoJsonDataSource, UrlTemplateImageryProvider } from 'cesium';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import { useStore } from '../../store/useStore';
import type { GeoJSONGeometry } from '../../types';

interface GlobeViewProps {
  onGeometrySelect?: (geometry: GeoJSONGeometry) => void;
}

export function GlobeView({ onGeometrySelect }: GlobeViewProps) {
  const { investigation, setGeometry, setActivePanel } = useStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const selectionHandlerRef = useRef<ScreenSpaceEventHandler | null>(null);
  const drawHandlerRef = useRef<ScreenSpaceEventHandler | null>(null);
  const drawPositionsRef = useRef<Cartesian3[]>([]);
  const drawPolygonRef = useRef<Entity | null>(null);
  const selectedEntityRef = useRef<Entity | null>(null);
  const [isDrawMode, setIsDrawMode] = useState(false);
  const [isBoundsMode, setIsBoundsMode] = useState(false);
  const [isAutoRotating, setIsAutoRotating] = useState(false);
  const [selectedRegionName, setSelectedRegionName] = useState('');
  const boundsStartRef = useRef<Cartesian3 | null>(null);
  const boundsRectangleRef = useRef<Entity | null>(null);

  // Initialize viewer
  useEffect(() => {
    if (!containerRef.current || viewerRef.current) return;
    let cancelled = false;

    const initializeViewer = async () => {
      const viewer = new Viewer(containerRef.current, {
        animation: false,
        baseLayerPicker: false,
        fullscreenButton: false,
        geocoder: false,
        homeButton: false,
        infoBox: false,
        sceneModePicker: false,
        selectionIndicator: false,
        timeline: false,
        navigationHelpButton: false,
        navigationInstructionsInitiallyVisible: false,
        scene3DOnly: true,
        baseLayer: false,
        shadows: false,
        useDefaultRenderLoop: true,
        targetFrameRate: 60,
        showRenderLoopErrors: false,
        contextOptions: {
          webgl: {
            alpha: false,
            antialias: true,
            preserveDrawingBuffer: true,
          },
        },
        requestRenderMode: false,
        maximumRenderTimeChange: 0,
      });

    // Configure globe
    viewer.scene.globe.enableLighting = true;
    viewer.scene.globe.showGroundAtmosphere = true;
    viewer.scene.globe.atmosphereBrightnessShift = -0.2;
    viewer.scene.globe.atmosphereHueShift = 0;
    viewer.scene.globe.atmosphereSaturationShift = -0.1;
    viewer.scene.globe.baseColor = Color.fromCssColorString('#274563');
    viewer.scene.backgroundColor = Color.fromCssColorString('#030812');

    // Remove default imagery and add dark theme
    viewer.imageryLayers.removeAll();
    const imageryProvider = new UrlTemplateImageryProvider({
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      credit: 'Imagery © Esri, Maxar, Earthstar Geographics, and the GIS User Community',
      maximumLevel: 19,
    });
    imageryProvider.errorEvent.addEventListener((error) => {
      console.warn('Satellite tile request failed', { message: error.message, x: error.x, y: error.y, level: error.level });
    });
    viewer.imageryLayers.addImageryProvider(imageryProvider);

    // Set initial camera view
    viewer.camera.setView({
      destination: Cartesian3.fromDegrees(12, 20, 16500000),
      orientation: {
        heading: 0,
        pitch: -CesiumMath.PI_OVER_TWO,
        roll: 0,
      },
    });

    viewerRef.current = viewer;

    // Add clickable country outlines above the satellite imagery.
    const countryLayer = await addCountryBoundaries(viewer);
    if (cancelled || viewer.isDestroyed()) return;
    if (investigation.geometry) updateSelectedPolygon(viewer, investigation.geometry);

    // Add coordinate display
    addCoordinateDisplay(viewer);

    // Handle selection events
    const handler = new ScreenSpaceEventHandler(viewer.canvas);
    selectionHandlerRef.current = handler;
    handler.setInputAction((movement) => {
      const picked = viewer.scene.pick(movement.position);
      const pickedEntity = defined(picked) ? (picked.id as Entity | undefined) : undefined;
      if (!drawHandlerRef.current && pickedEntity?.polygon && countryLayer?.entities.contains(pickedEntity)) {
        handleEntitySelection(pickedEntity);
      }
    }, ScreenSpaceEventType.LEFT_CLICK);

    };

    void initializeViewer();
    return () => {
      cancelled = true;
      selectionHandlerRef.current?.destroy();
      selectionHandlerRef.current = null;
      viewerRef.current?.destroy();
      viewerRef.current = null;
    };
  }, []);

  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || !isAutoRotating) return;
    return viewer.scene.preRender.addEventListener(() => viewer.camera.rotateRight(0.00018));
  }, [isAutoRotating]);

  useEffect(() => {
    const handleRegionName = (event: Event) => setSelectedRegionName((event as CustomEvent<{ name: string }>).detail.name);
    window.addEventListener('globe-region-name', handleRegionName);
    return () => window.removeEventListener('globe-region-name', handleRegionName);
  }, []);

  const addCountryBoundaries = async (viewer: Viewer) => {
    try {
      const dataSource = await GeoJsonDataSource.load(
        'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson',
        {
          stroke: Color.fromCssColorString('#c4e9ff').withAlpha(0.58),
          strokeWidth: 1,
          fill: Color.TRANSPARENT,
          clampToGround: true,
        }
      );
      if (viewer.isDestroyed()) {
        return null;
      }
      viewer.dataSources.add(dataSource);
      dataSource.entities.values.forEach((entity) => {
        if (entity.polygon) {
          entity.polygon.material = Color.WHITE.withAlpha(0.015);
          entity.polygon.outline = true;
          entity.polygon.outlineColor = Color.fromCssColorString('#c4e9ff').withAlpha(0.58);
          entity.polygon.outlineWidth = 1;
          entity.polygon.height = 0;
        }
      });
      return dataSource;
    } catch (err) {
      console.warn('Could not load country boundaries:', err);
      return null;
    }
  };

  const addCoordinateDisplay = (viewer: Viewer) => {
    const coordsDiv = document.createElement('div');
    coordsDiv.className = 'absolute bottom-20 left-4 z-20 bg-hypnen-navy/90 backdrop-blur-sm border border-hypnen-border rounded-lg px-3 py-2 text-xs font-mono text-hypnen-text-dim pointer-events-none';
    coordsDiv.style.fontFamily = 'JetBrains Mono, monospace';
    coordsDiv.textContent = 'Lon: 0.000°, Lat: 0.000°';
    viewer.container.appendChild(coordsDiv);

    viewer.camera.changed.addEventListener(() => {
      const cartographic = viewer.camera.positionCartographic;
      if (cartographic) {
        const lon = CesiumMath.toDegrees(cartographic.longitude).toFixed(3);
        const lat = CesiumMath.toDegrees(cartographic.latitude).toFixed(3);
        coordsDiv.textContent = `Lon: ${lon}°, Lat: ${lat}°`;
      }
    });
  };

  const handleEntitySelection = (entity: Entity) => {
    if (entity.polygon?.hierarchy && viewerRef.current) {
      const hierarchy = entity.polygon.hierarchy.getValue(viewerRef.current!.clock.currentTime);
      if (hierarchy && hierarchy.positions) {
        const positions = hierarchy.positions;
        const coordinates = positions.map((pos: Cartesian3) => {
          const cartographic = viewerRef.current!.scene.globe.ellipsoid.cartesianToCartographic(pos);
          return [CesiumMath.toDegrees(cartographic.longitude), CesiumMath.toDegrees(cartographic.latitude)];
        });
        // Close the polygon
        coordinates.push(coordinates[0]);

        const props = entity.properties;
        const name = props?.ADMIN?.getValue(viewerRef.current.clock.currentTime)
          ?? props?.name?.getValue(viewerRef.current.clock.currentTime)
          ?? props?.NAME?.getValue(viewerRef.current.clock.currentTime)
          ?? 'Selected region';
        const geometry: GeoJSONGeometry = { type: 'Polygon', coordinates: [coordinates] };

        setSelectedRegionName(String(name));
        setGeometry(geometry);
        onGeometrySelect?.(geometry);
      }
    }
  };

  // Watch for geometry changes from sidebar
  useEffect(() => {
    if (viewerRef.current && investigation.geometry) {
      updateSelectedPolygon(viewerRef.current, investigation.geometry);
    }
  }, [investigation.geometry]);

  const updateSelectedPolygon = (viewer: Viewer, geometry: GeoJSONGeometry) => {
    // Remove existing selection
    if (selectedEntityRef.current) {
      viewer.entities.remove(selectedEntityRef.current);
    }

    if (geometry.type === 'Polygon' && geometry.coordinates) {
      const positions = geometry.coordinates[0].map((coord: number[]) =>
        Cartesian3.fromDegrees(coord[0], coord[1])
      );

      const entity = viewer.entities.add({
        name: 'Selected Region',
        polygon: {
          hierarchy: new PolygonHierarchy(positions),
          material: Color.fromCssColorString('#00d4ff').withAlpha(0.4),
          outline: true,
          outlineColor: Color.fromCssColorString('#00d4ff'),
          outlineWidth: 2,
          clampToGround: true,
        },
      });

      selectedEntityRef.current = entity;
      viewer.flyTo(entity, { duration: 1.4 });
    } else if (geometry.type === 'MultiPolygon' && geometry.coordinates) {
      // Handle MultiPolygon - create multiple entities
      geometry.coordinates.forEach((polygonCoords, idx) => {
        const positions = polygonCoords[0].map((coord: number[]) =>
          Cartesian3.fromDegrees(coord[0], coord[1])
        );

        const entity = viewer.entities.add({
          name: `Selected Region ${idx + 1}`,
          polygon: {
            hierarchy: new PolygonHierarchy(positions),
            material: Color.fromCssColorString('#00d4ff').withAlpha(0.4),
            outline: true,
            outlineColor: Color.fromCssColorString('#00d4ff'),
            outlineWidth: 2,
            clampToGround: true,
          },
        });

        if (idx === 0) selectedEntityRef.current = entity;
      });
      viewer.flyTo(viewer.entities, { duration: 1.4 });
    }
  };

  // Handle draw mode
  useEffect(() => {
    const handleDrawMode = (event: CustomEvent) => {
      const { enable } = event.detail;
      setIsDrawMode(enable);
      if (enable) {
        enableDrawMode();
      } else {
        disableDrawMode();
      }
    };

    const handleUndoPoint = () => {
      if (drawPositionsRef.current.length > 0) {
        drawPositionsRef.current.pop();
        updateDrawPolygon();
      }
    };

    const handleClearDrawing = () => {
      drawPositionsRef.current = [];
      updateDrawPolygon();
    };

    window.addEventListener('globe-draw-mode', handleDrawMode as EventListener);
    window.addEventListener('globe-undo-last-point', handleUndoPoint);
    window.addEventListener('globe-clear-drawing', handleClearDrawing);

    return () => {
      window.removeEventListener('globe-draw-mode', handleDrawMode as EventListener);
      window.removeEventListener('globe-undo-last-point', handleUndoPoint);
      window.removeEventListener('globe-clear-drawing', handleClearDrawing);
    };
  }, []);

  const enableDrawMode = () => {
    if (!viewerRef.current) return;

    // Create draw handler
    const handler = new ScreenSpaceEventHandler(viewerRef.current.canvas);
    drawHandlerRef.current = handler;

    handler.setInputAction((movement) => {
      const cartesian = viewerRef.current!.scene.globe.pick(
        viewerRef.current!.camera.getPickRay(movement.position),
        viewerRef.current!.scene
      );

      if (cartesian) {
        drawPositionsRef.current.push(cartesian);
        updateDrawPolygon();
      }
    }, ScreenSpaceEventType.LEFT_CLICK);

    handler.setInputAction(() => {
      if (drawPositionsRef.current.length >= 3) {
        finalizeDrawPolygon();
      }
    }, ScreenSpaceEventType.LEFT_DOUBLE_CLICK);
  };

  const disableDrawMode = () => {
    if (drawHandlerRef.current) {
      drawHandlerRef.current.destroy();
      drawHandlerRef.current = null;
    }
    drawPositionsRef.current = [];
    if (drawPolygonRef.current && viewerRef.current) {
      viewerRef.current.entities.remove(drawPolygonRef.current);
      drawPolygonRef.current = null;
    }
  };

  const updateDrawPolygon = () => {
    if (!viewerRef.current) return;

    if (drawPolygonRef.current) {
      viewerRef.current.entities.remove(drawPolygonRef.current);
    }

    if (drawPositionsRef.current.length > 0) {
      const positions = [...drawPositionsRef.current];
      // Close polygon for display if we have 3+ points
      if (positions.length >= 3) {
        positions.push(positions[0]);
      }

      drawPolygonRef.current = viewerRef.current.entities.add({
        name: 'Drawing Polygon',
        polyline: {
          positions: positions,
          width: 3,
          material: Color.fromCssColorString('#ff6b35'),
          clampToGround: true,
        },
        polygon: positions.length >= 4 ? {
          hierarchy: new PolygonHierarchy(positions.slice(0, -1)),
          material: Color.fromCssColorString('#ff6b35').withAlpha(0.2),
          outline: true,
          outlineColor: Color.fromCssColorString('#ff6b35'),
          outlineWidth: 2,
          clampToGround: true,
        } : undefined,
      });
    }
  };

  const finalizeDrawPolygon = () => {
    if (drawPositionsRef.current.length < 3 || !viewerRef.current) return;

    const positions = [...drawPositionsRef.current];
    const coordinates = positions.map((pos) => {
      const cartographic = viewerRef.current!.scene.globe.ellipsoid.cartesianToCartographic(pos);
      return [CesiumMath.toDegrees(cartographic.longitude), CesiumMath.toDegrees(cartographic.latitude)];
    });
    coordinates.push(coordinates[0]);

    const geometry: GeoJSONGeometry = {
      type: 'Polygon',
      coordinates: [coordinates],
    };

    setGeometry(geometry);
    onGeometrySelect?.(geometry);

    // Clean up drawing
    disableDrawMode();
    window.dispatchEvent(new CustomEvent('globe-draw-mode', { detail: { enable: false } }));
  };

  // Handle bounds mode
  useEffect(() => {
    const handleBoundsMode = (event: CustomEvent) => {
      const { enable } = event.detail;
      setIsBoundsMode(enable);
      if (enable) {
        enableBoundsMode();
      } else {
        disableBoundsMode();
      }
    };

    window.addEventListener('globe-bounds-mode', handleBoundsMode as EventListener);

    return () => {
      window.removeEventListener('globe-bounds-mode', handleBoundsMode as EventListener);
    };
  }, []);

  const enableBoundsMode = () => {
    if (!viewerRef.current) return;

    const handler = new ScreenSpaceEventHandler(viewerRef.current.canvas);
    drawHandlerRef.current = handler;

    handler.setInputAction((movement) => {
      const cartesian = viewerRef.current!.scene.globe.pick(
        viewerRef.current!.camera.getPickRay(movement.position),
        viewerRef.current!.scene
      );

      if (cartesian) {
        boundsStartRef.current = cartesian;
      }
    }, ScreenSpaceEventType.LEFT_DOWN);

    handler.setInputAction((movement) => {
      if (!boundsStartRef.current) return;

      const cartesian = viewerRef.current!.scene.globe.pick(
        viewerRef.current!.camera.getPickRay(movement.endPosition),
        viewerRef.current!.scene
      );

      if (cartesian) {
        updateBoundsRectangle(boundsStartRef.current, cartesian);
      }
    }, ScreenSpaceEventType.MOUSE_MOVE);

    handler.setInputAction(() => {
      if (boundsStartRef.current && boundsRectangleRef.current) {
        finalizeBoundsRectangle();
      }
      boundsStartRef.current = null;
    }, ScreenSpaceEventType.LEFT_UP);
  };

  const disableBoundsMode = () => {
    if (drawHandlerRef.current) {
      drawHandlerRef.current.destroy();
      drawHandlerRef.current = null;
    }
    boundsStartRef.current = null;
    if (boundsRectangleRef.current && viewerRef.current) {
      viewerRef.current.entities.remove(boundsRectangleRef.current);
      boundsRectangleRef.current = null;
    }
  };

  const updateBoundsRectangle = (start: Cartesian3, end: Cartesian3) => {
    if (!viewerRef.current) return;

    const startCarto = viewerRef.current.scene.globe.ellipsoid.cartesianToCartographic(start);
    const endCarto = viewerRef.current.scene.globe.ellipsoid.cartesianToCartographic(end);

    const west = Math.min(CesiumMath.toDegrees(startCarto.longitude), CesiumMath.toDegrees(endCarto.longitude));
    const east = Math.max(CesiumMath.toDegrees(startCarto.longitude), CesiumMath.toDegrees(endCarto.longitude));
    const south = Math.min(CesiumMath.toDegrees(startCarto.latitude), CesiumMath.toDegrees(endCarto.latitude));
    const north = Math.max(CesiumMath.toDegrees(startCarto.latitude), CesiumMath.toDegrees(endCarto.latitude));

    if (boundsRectangleRef.current) {
      viewerRef.current.entities.remove(boundsRectangleRef.current);
    }

    boundsRectangleRef.current = viewerRef.current.entities.add({
      name: 'Bounds Rectangle',
      rectangle: {
        coordinates: Rectangle.fromDegrees(west, south, east, north),
        material: Color.fromCssColorString('#1e90ff').withAlpha(0.2),
        outline: true,
        outlineColor: Color.fromCssColorString('#1e90ff'),
        outlineWidth: 2,
      },
    });
  };

  const finalizeBoundsRectangle = () => {
    if (!boundsRectangleRef.current || !viewerRef.current) return;

    const rectangle = boundsRectangleRef.current.rectangle!.coordinates.getValue(viewerRef.current.clock.currentTime);
    if (!rectangle) return;

    const west = CesiumMath.toDegrees(rectangle.west);
    const south = CesiumMath.toDegrees(rectangle.south);
    const east = CesiumMath.toDegrees(rectangle.east);
    const north = CesiumMath.toDegrees(rectangle.north);

    const coordinates = [
      [west, south],
      [east, south],
      [east, north],
      [west, north],
      [west, south],
    ];

    const geometry: GeoJSONGeometry = {
      type: 'Polygon',
      coordinates: [coordinates],
    };

    setGeometry(geometry);
    onGeometrySelect?.(geometry);

    disableBoundsMode();
    window.dispatchEvent(new CustomEvent('globe-bounds-mode', { detail: { enable: false } }));
  };

  // Handle clear selection from sidebar
  useEffect(() => {
    const handleClearSelection = () => {
      if (selectedEntityRef.current && viewerRef.current) {
        viewerRef.current.entities.remove(selectedEntityRef.current);
        selectedEntityRef.current = null;
      }
    };

    window.addEventListener('globe-clear-selection', handleClearSelection);
    return () => window.removeEventListener('globe-clear-selection', handleClearSelection);
  }, []);

  return (
    <div className="relative h-full w-full">
      <div ref={containerRef} className="h-full w-full" />

      <div className="absolute left-4 top-4 z-20 inline-flex items-center rounded-xl border border-white/10 bg-[#081323]/90 p-1 shadow-xl backdrop-blur-xl">
        <button onClick={() => setActivePanel('globe')} className="flex items-center gap-2 rounded-lg bg-sky-500 px-4 py-2 text-sm font-semibold text-slate-950 shadow-lg shadow-sky-500/20"><span aria-hidden="true">◎</span> 3D Globe</button>
        <button onClick={() => setActivePanel('map')} className="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-slate-300 transition hover:text-white"><span aria-hidden="true">▧</span> 2D Map</button>
      </div>
      <div className="absolute left-4 top-1/2 z-20 flex -translate-y-1/2 flex-col overflow-hidden rounded-xl border border-white/10 bg-[#081323]/90 shadow-xl backdrop-blur-xl">
        <button onClick={() => viewerRef.current?.camera.flyHome(1.2)} className="globe-control" title="Reset globe view" aria-label="Reset globe view">⌂</button>
        <button onClick={() => viewerRef.current?.camera.zoomIn(1200000)} className="globe-control text-xl" title="Zoom in" aria-label="Zoom in">+</button>
        <button onClick={() => viewerRef.current?.camera.zoomOut(1200000)} className="globe-control text-xl" title="Zoom out" aria-label="Zoom out">−</button>
        <button onClick={() => setIsAutoRotating((value) => !value)} className="globe-control" title={isAutoRotating ? 'Pause globe rotation' : 'Auto-rotate globe'} aria-label={isAutoRotating ? 'Pause globe rotation' : 'Auto-rotate globe'}>⟳</button>
      </div>
      <div className="absolute bottom-5 left-1/2 z-20 w-[min(92%,440px)] -translate-x-1/2 rounded-2xl border border-white/10 bg-[#081323]/90 px-4 py-3 shadow-2xl backdrop-blur-xl">
        {investigation.geometry ? <div className="flex items-start gap-3"><span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-emerald-400/15 text-sm text-emerald-300">✓</span><div className="min-w-0 flex-1"><div className="text-sm font-semibold text-white">Region selected{selectedRegionName ? `: ${selectedRegionName}` : ''}</div><div className="mt-1 text-xs text-slate-400">{formatGeometrySummary(investigation.geometry)}</div></div><button onClick={() => { setGeometry(null); setSelectedRegionName(''); window.dispatchEvent(new CustomEvent('globe-clear-selection')); }} className="text-lg leading-none text-slate-400 transition hover:text-white" aria-label="Clear selected region">×</button></div> : <div className="flex items-center gap-3 text-sm text-slate-300"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-sky-400/15 text-sky-300">◎</span><span><strong className="font-semibold text-white">Choose a region</strong><span className="text-slate-400"> · click a country, search a place, or draw on the globe</span></span></div>}
      </div>

      {/* Mode Indicators */}
      {isDrawMode && (
        <div className="absolute top-20 left-4 right-4 z-30 animate-slide-up">
          <div className="max-w-md mx-auto card border-hypnen-accent/50 bg-hypnen-accent/10 p-3 flex items-center gap-3">
            <svg className="w-5 h-5 text-hypnen-accent flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
            </svg>
            <span className="text-sm font-medium text-hypnen-text">Draw Mode: Click to add vertices. Double-click to complete.</span>
            <button
              onClick={() => {
                window.dispatchEvent(new CustomEvent('globe-clear-drawing'));
                window.dispatchEvent(new CustomEvent('globe-draw-mode', { detail: { enable: false } }));
              }}
              className="ml-auto px-3 py-1 text-xs bg-hypnen-card border border-hypnen-border rounded hover:border-hypnen-red/30 text-hypnen-red transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {isBoundsMode && (
        <div className="absolute top-20 left-4 right-4 z-30 animate-slide-up">
          <div className="max-w-md mx-auto card border-hypnen-blue/50 bg-hypnen-blue/10 p-3 flex items-center gap-3">
            <svg className="w-5 h-5 text-hypnen-blue flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 16h18M3 8h18m0 0V4a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2h14a2 2 0 002-2V8" />
            </svg>
            <span className="text-sm font-medium text-hypnen-text">Rectangle Mode: Click and drag to draw region.</span>
            <button onClick={() => window.dispatchEvent(new CustomEvent('globe-bounds-mode', { detail: { enable: false } }))} className="ml-auto rounded border border-hypnen-border px-3 py-1 text-xs text-slate-300 hover:text-white">Cancel</button>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-5 right-4 z-20 card p-3 min-w-[180px] bg-[#081323]/85 backdrop-blur-xl">
        <div className="text-xs font-medium text-hypnen-text mb-2">Map Layers</div>
        <div className="space-y-2 text-xs">
          <div className="flex items-center gap-2 text-hypnen-text-dim">
            <div className="w-4 h-4 rounded border border-hypnen-border/50 bg-hypnen-card" />
            <span>Countries</span>
          </div>
          <div className="flex items-center gap-2 text-hypnen-cyan">
            <div className="w-4 h-4 rounded bg-hypnen-cyan/40 border border-hypnen-cyan" />
            <span>Selected Region</span>
          </div>
          <div className="flex items-center gap-2 text-hypnen-accent">
            <div className="w-4 h-4 rounded border-2 border-hypnen-accent" />
            <span>Drawing</span>
          </div>
          <div className="flex items-center gap-2 text-hypnen-blue">
            <div className="w-4 h-4 rounded bg-hypnen-blue/40 border border-hypnen-blue" />
            <span>Rectangle Selection</span>
          </div>
        </div>
      </div>

      {/* View Controls */}
      <div className="hidden">
        <button
          onClick={() => viewerRef.current?.camera.flyTo({
            destination: Cartesian3.fromDegrees(0, 20, 15000000),
            duration: 2,
          })}
          className="card p-2 rounded-lg hover:bg-hypnen-cyan/10 hover:border-hypnen-cyan/30 transition-all"
          title="Reset View"
        >
          <svg className="w-5 h-5 text-hypnen-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </button>
        <button
          onClick={() => {
            if (selectedEntityRef.current && viewerRef.current) {
              viewerRef.current.camera.flyTo(selectedEntityRef.current, { duration: 2 });
            }
          }}
          className="card p-2 rounded-lg hover:bg-hypnen-cyan/10 hover:border-hypnen-cyan/30 transition-all opacity-50"
          title="Zoom to Selection"
          disabled={!selectedEntityRef.current}
        >
          <svg className="w-5 h-5 text-hypnen-text" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
          </svg>
        </button>
      </div>
    </div>
  );
}

function formatGeometrySummary(geometry: GeoJSONGeometry) {
  const points: number[][] = [];
  const visit = (value: any) => {
    if (Array.isArray(value) && value.length >= 2 && typeof value[0] === 'number' && typeof value[1] === 'number') points.push(value as number[]);
    else if (Array.isArray(value)) value.forEach(visit);
  };
  visit(geometry.coordinates ?? geometry.geometry?.coordinates);
  if (!points.length) return `${geometry.type} region`;
  const bounds = points.reduce((value, [lon, lat]) => ({
    west: Math.min(value.west, lon), east: Math.max(value.east, lon),
    south: Math.min(value.south, lat), north: Math.max(value.north, lat),
  }), { west: Infinity, east: -Infinity, south: Infinity, north: -Infinity });
  const format = (value: number, axis: 'lat' | 'lon') => `${Math.abs(value).toFixed(1)}°${axis === 'lat' ? (value < 0 ? 'S' : 'N') : (value < 0 ? 'W' : 'E')}`;
  return `Coordinates: ${format(bounds.south, 'lat')} to ${format(bounds.north, 'lat')} · ${format(bounds.west, 'lon')} to ${format(bounds.east, 'lon')}`;
}
