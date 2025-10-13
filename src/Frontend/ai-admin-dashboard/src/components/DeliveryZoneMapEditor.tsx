/**
 * DeliveryZoneMapEditor Component
 *
 * Visual geo-fencing editor for delivery zones using Mapbox GL JS
 *
 * Features:
 * - Interactive polygon drawing
 * - Real-time zone statistics (area, perimeter)
 * - Validation (polygon must contain store)
 * - GeoJSON output for database storage
 * - Mobile-friendly touch interactions
 *
 * Technology: Mapbox GL JS + Mapbox Draw + Turf.js
 */

import React, { useRef, useCallback, useState, useEffect } from 'react';
import Map, { Marker, Source, Layer, MapRef } from 'react-map-gl';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import type { DrawCreateEvent, DrawUpdateEvent, DrawDeleteEvent } from '@mapbox/mapbox-gl-draw';
import * as turf from '@turf/turf';
import { MapPin, AlertCircle, Info, Trash2, Edit3, Save } from 'lucide-react';
import 'mapbox-gl/dist/mapbox-gl.css';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';

// GeoJSON types
export interface DeliveryZoneGeoJSON {
  type: 'Polygon';
  coordinates: number[][][];  // [[[lng, lat], [lng, lat], ...]]
}

export interface ZoneStatistics {
  area_km2: number;
  perimeter_km: number;
  approximate_radius_km: number;
  point_count: number;
}

export interface DeliveryZoneMapEditorProps {
  storeCoordinates: { latitude: number; longitude: number };
  initialZone?: DeliveryZoneGeoJSON | null;
  onChange: (zone: DeliveryZoneGeoJSON | null) => void;
  onStatsChange?: (stats: ZoneStatistics | null) => void;
  className?: string;
  disabled?: boolean;
  mapboxToken?: string;
}

// Mapbox Draw styles (green for delivery zone)
const drawStyles = [
  // Polygon fill
  {
    id: 'gl-draw-polygon-fill',
    type: 'fill',
    filter: ['all', ['==', '$type', 'Polygon'], ['!=', 'mode', 'static']],
    paint: {
      'fill-color': '#4CAF50',
      'fill-outline-color': '#4CAF50',
      'fill-opacity': 0.3,
    },
  },
  // Polygon outline
  {
    id: 'gl-draw-polygon-stroke-active',
    type: 'line',
    filter: ['all', ['==', '$type', 'Polygon'], ['!=', 'mode', 'static']],
    layout: {
      'line-cap': 'round',
      'line-join': 'round',
    },
    paint: {
      'line-color': '#4CAF50',
      'line-width': 2,
    },
  },
  // Vertex points
  {
    id: 'gl-draw-polygon-and-line-vertex-active',
    type: 'circle',
    filter: ['all', ['==', 'meta', 'vertex'], ['!=', 'mode', 'static']],
    paint: {
      'circle-radius': 6,
      'circle-color': '#4CAF50',
      'circle-stroke-color': '#FFF',
      'circle-stroke-width': 2,
    },
  },
];

export const DeliveryZoneMapEditor: React.FC<DeliveryZoneMapEditorProps> = ({
  storeCoordinates,
  initialZone,
  onChange,
  onStatsChange,
  className = '',
  disabled = false,
  mapboxToken,
}) => {
  const mapRef = useRef<MapRef>(null);
  const drawRef = useRef<MapboxDraw | null>(null);

  const [currentZone, setCurrentZone] = useState<DeliveryZoneGeoJSON | null>(initialZone || null);
  const [stats, setStats] = useState<ZoneStatistics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawMode, setDrawMode] = useState<'draw' | 'edit' | null>(null);

  // Get Mapbox token from props or environment
  const MAPBOX_TOKEN = mapboxToken ||
    import.meta.env.VITE_MAPBOX_ACCESS_TOKEN ||
    'pk.eyJ1IjoiY2hhcnJjeSIsImEiOiJja2llcXF5eXcxNWx4MnlxeHAzbmJnY3g2In0.FC98EHBZh2apYVTNiuyNKg';

  // Initialize Mapbox Draw when map loads
  const onMapLoad = useCallback(() => {
    if (!mapRef.current) return;

    const map = mapRef.current.getMap();

    // Create Mapbox Draw instance
    const draw = new MapboxDraw({
      displayControlsDefault: false,
      controls: {},
      styles: drawStyles as any,
      defaultMode: 'simple_select',
    });

    map.addControl(draw as any, 'top-left');
    drawRef.current = draw;

    // Load initial zone if provided
    if (initialZone) {
      draw.add({
        type: 'Feature',
        properties: {},
        geometry: initialZone,
      } as any);
      calculateStats(initialZone);
    }

    // Add event listeners
    map.on('draw.create', handleDrawCreate as any);
    map.on('draw.update', handleDrawUpdate as any);
    map.on('draw.delete', handleDrawDelete as any);

  }, [initialZone]);

  // Handle polygon creation
  const handleDrawCreate = useCallback((e: DrawCreateEvent) => {
    const features = e.features;
    if (features.length === 0) return;

    const feature = features[0];
    if (feature.geometry.type !== 'Polygon') return;

    const polygon = feature.geometry as DeliveryZoneGeoJSON;

    // Validate polygon
    const validation = validatePolygon(polygon);
    if (!validation.valid) {
      setError(validation.error || 'Invalid polygon');
      // Remove invalid polygon
      if (drawRef.current) {
        drawRef.current.delete(feature.id as string);
      }
      return;
    }

    setError(null);
    setCurrentZone(polygon);
    onChange(polygon);
    calculateStats(polygon);
    setIsDrawing(false);
    setDrawMode(null);
  }, [onChange, storeCoordinates]);

  // Handle polygon update
  const handleDrawUpdate = useCallback((e: DrawUpdateEvent) => {
    const features = e.features;
    if (features.length === 0) return;

    const feature = features[0];
    if (feature.geometry.type !== 'Polygon') return;

    const polygon = feature.geometry as DeliveryZoneGeoJSON;

    // Validate polygon
    const validation = validatePolygon(polygon);
    if (!validation.valid) {
      setError(validation.error || 'Invalid polygon');
      return;
    }

    setError(null);
    setCurrentZone(polygon);
    onChange(polygon);
    calculateStats(polygon);
  }, [onChange, storeCoordinates]);

  // Handle polygon deletion
  const handleDrawDelete = useCallback((e: DrawDeleteEvent) => {
    setCurrentZone(null);
    setStats(null);
    setError(null);
    onChange(null);
    if (onStatsChange) {
      onStatsChange(null);
    }
    setDrawMode(null);
  }, [onChange, onStatsChange]);

  // Validate polygon
  const validatePolygon = (polygon: DeliveryZoneGeoJSON): { valid: boolean; error?: string } => {
    try {
      // Check if polygon is valid GeoJSON
      const turfPolygon = turf.polygon(polygon.coordinates);

      // Check if polygon contains the store location
      const storePoint = turf.point([storeCoordinates.longitude, storeCoordinates.latitude]);
      const containsStore = turf.booleanPointInPolygon(storePoint, turfPolygon);

      if (!containsStore) {
        return {
          valid: false,
          error: 'Delivery zone must contain the store location',
        };
      }

      // Check for self-intersections
      const kinks = turf.kinks(turfPolygon);
      if (kinks.features.length > 0) {
        return {
          valid: false,
          error: 'Polygon cannot intersect itself',
        };
      }

      // Check area (minimum 0.1 km², maximum 500 km²)
      const area = turf.area(turfPolygon) / 1_000_000; // Convert to km²
      if (area < 0.1) {
        return {
          valid: false,
          error: 'Delivery zone is too small (minimum 0.1 km²)',
        };
      }
      if (area > 500) {
        return {
          valid: false,
          error: 'Delivery zone is too large (maximum 500 km²)',
        };
      }

      // Check point count (maximum 100 points)
      const pointCount = polygon.coordinates[0].length;
      if (pointCount > 100) {
        return {
          valid: false,
          error: 'Polygon has too many points (maximum 100)',
        };
      }

      return { valid: true };
    } catch (err) {
      return {
        valid: false,
        error: 'Invalid polygon format',
      };
    }
  };

  // Calculate zone statistics
  const calculateStats = (polygon: DeliveryZoneGeoJSON) => {
    try {
      const turfPolygon = turf.polygon(polygon.coordinates);

      // Calculate area in km²
      const area_km2 = turf.area(turfPolygon) / 1_000_000;

      // Calculate perimeter in km
      const perimeter_km = turf.length(turf.polygonToLine(turfPolygon), { units: 'kilometers' });

      // Calculate approximate radius (for reference)
      const approximate_radius_km = Math.sqrt(area_km2 / Math.PI);

      // Point count
      const point_count = polygon.coordinates[0].length;

      const statistics: ZoneStatistics = {
        area_km2: Math.round(area_km2 * 10) / 10,
        perimeter_km: Math.round(perimeter_km * 10) / 10,
        approximate_radius_km: Math.round(approximate_radius_km * 10) / 10,
        point_count,
      };

      setStats(statistics);
      if (onStatsChange) {
        onStatsChange(statistics);
      }
    } catch (err) {
      console.error('Error calculating stats:', err);
    }
  };

  // Start drawing mode
  const startDrawing = () => {
    if (!drawRef.current || disabled) return;

    // Delete existing polygon if any
    const existingFeatures = drawRef.current.getAll();
    existingFeatures.features.forEach((feature: any) => {
      drawRef.current?.delete(feature.id);
    });

    // Enter draw mode
    drawRef.current.changeMode('draw_polygon');
    setIsDrawing(true);
    setDrawMode('draw');
    setError(null);
  };

  // Start edit mode
  const startEditing = () => {
    if (!drawRef.current || !currentZone || disabled) return;

    const existingFeatures = drawRef.current.getAll();
    if (existingFeatures.features.length > 0) {
      const featureId = existingFeatures.features[0].id;
      drawRef.current.changeMode('direct_select', { featureId });
      setDrawMode('edit');
    }
  };

  // Delete zone
  const deleteZone = () => {
    if (!drawRef.current || disabled) return;

    const existingFeatures = drawRef.current.getAll();
    existingFeatures.features.forEach((feature: any) => {
      drawRef.current?.delete(feature.id);
    });

    setCurrentZone(null);
    setStats(null);
    setError(null);
    setDrawMode(null);
    onChange(null);
    if (onStatsChange) {
      onStatsChange(null);
    }
  };

  return (
    <div className={`delivery-zone-map-editor ${className}`}>
      {/* Map Container */}
      <div className={`relative bg-gray-100 dark:bg-gray-800 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700 ${className}`}>
        <Map
          ref={mapRef}
          mapboxAccessToken={MAPBOX_TOKEN}
          initialViewState={{
            longitude: storeCoordinates.longitude,
            latitude: storeCoordinates.latitude,
            zoom: 13,
          }}
          style={{ width: '100%', height: '100%' }}
          mapStyle="mapbox://styles/mapbox/streets-v12"
          onLoad={onMapLoad}
        >
          {/* Store Marker */}
          <Marker
            longitude={storeCoordinates.longitude}
            latitude={storeCoordinates.latitude}
            anchor="bottom"
          >
            <div className="relative">
              <MapPin className="w-8 h-8 text-red-500 fill-red-500 drop-shadow-lg" />
              <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap bg-white dark:bg-gray-800 px-2 py-1 rounded shadow-lg text-xs font-medium">
                Store
              </div>
            </div>
          </Marker>
        </Map>

        {/* Drawing Tools */}
        {!disabled && (
          <div className="absolute top-4 right-4 flex flex-col gap-2">
            {!currentZone ? (
              <button
                onClick={startDrawing}
                disabled={isDrawing}
                className="bg-white dark:bg-gray-800 px-4 py-2 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 text-sm font-medium"
                title="Draw delivery zone"
              >
                <Edit3 className="w-4 h-4" />
                {isDrawing ? 'Drawing...' : 'Draw Zone'}
              </button>
            ) : (
              <>
                <button
                  onClick={startEditing}
                  className="bg-white dark:bg-gray-800 px-4 py-2 rounded-lg shadow-lg border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center gap-2 text-sm font-medium"
                  title="Edit delivery zone"
                >
                  <Edit3 className="w-4 h-4" />
                  Edit Zone
                </button>
                <button
                  onClick={deleteZone}
                  className="bg-white dark:bg-gray-800 px-4 py-2 rounded-lg shadow-lg border border-red-200 dark:border-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400 flex items-center gap-2 text-sm font-medium"
                  title="Delete delivery zone"
                >
                  <Trash2 className="w-4 h-4" />
                  Delete
                </button>
              </>
            )}
          </div>
        )}

        {/* Helper Text */}
        {isDrawing && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-blue-500 text-white px-4 py-2 rounded-lg shadow-lg text-sm font-medium flex items-center gap-2">
            <Info className="w-4 h-4" />
            Click on map to add points, double-click to finish
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3 flex items-start gap-2">
          <AlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-800 dark:text-red-200">Invalid Delivery Zone</p>
            <p className="text-sm text-red-600 dark:text-red-400 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Zone Statistics */}
      {stats && currentZone && (
        <div className="mt-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
          <h4 className="text-sm font-semibold text-green-900 dark:text-green-100 mb-2 flex items-center gap-2">
            <MapPin className="w-4 h-4" />
            Delivery Zone Statistics
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            <div>
              <p className="text-green-600 dark:text-green-400 font-medium">Area</p>
              <p className="text-green-900 dark:text-green-100 font-bold">{stats.area_km2} km²</p>
            </div>
            <div>
              <p className="text-green-600 dark:text-green-400 font-medium">Perimeter</p>
              <p className="text-green-900 dark:text-green-100 font-bold">{stats.perimeter_km} km</p>
            </div>
            <div>
              <p className="text-green-600 dark:text-green-400 font-medium">Approx. Radius</p>
              <p className="text-green-900 dark:text-green-100 font-bold">{stats.approximate_radius_km} km</p>
            </div>
            <div>
              <p className="text-green-600 dark:text-green-400 font-medium">Points</p>
              <p className="text-green-900 dark:text-green-100 font-bold">{stats.point_count}</p>
            </div>
          </div>
          <p className="text-xs text-green-600 dark:text-green-400 mt-2">
            💡 Approximate delivery time: {Math.round(stats.approximate_radius_km * 15)}-{Math.round(stats.approximate_radius_km * 20)} minutes
          </p>
        </div>
      )}

      {/* Helper Text */}
      {!currentZone && !disabled && (
        <div className="mt-3 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-3 flex items-start gap-2">
          <Info className="w-5 h-5 text-gray-500 dark:text-gray-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 text-sm text-gray-600 dark:text-gray-400">
            <p className="font-medium text-gray-900 dark:text-gray-100 mb-1">No delivery zone defined</p>
            <p>Click "Draw Zone" to create a custom delivery area around your store. The zone must contain the store location.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default DeliveryZoneMapEditor;
