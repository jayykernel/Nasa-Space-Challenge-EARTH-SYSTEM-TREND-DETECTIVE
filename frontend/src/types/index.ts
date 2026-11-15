/** Shared TypeScript types for Earth System Trend Detective */

export interface GeoJSONGeometry {
  type: 'Point' | 'Polygon' | 'MultiPolygon' | 'Feature' | 'FeatureCollection';
  coordinates?: any;
  geometry?: any;
  properties?: any;
  features?: any;
}

export interface TimeRange {
  start: string;
  end: string;
}

export interface InvestigationRequest {
  variables: string[];
  geometry: GeoJSONGeometry;
  time_range: TimeRange;
  temporal_resolution: 'daily' | 'monthly' | 'annual' | 'seasonal';
}

export interface VariableInfo {
  key: string;
  display_name: string;
  description: string;
  unit: string;
  data_source: string;
  available_coverage: string;
  spatial_resolution: string;
  scientific_explanation: string;
  dataset_ids: string[];
}

export interface DatasetInfo {
  feature_id: string;
  display_name: string;
  mission: string;
  dataset_short_name: string;
  collection_id: string;
  version: string;
  variable_name: string;
  units: string;
  spatial_resolution: string;
  temporal_resolution: string;
  historical_coverage: string;
  authentication_required: boolean;
  access_endpoint: string;
  processing_notes: string | null;
  description: string;
  acquisition_status?: string;
}

export interface InvestigationStatus {
  investigation_id: string;
  status: 'queued' | 'retrieving_data' | 'validating' | 'normalizing' | 'processing' | 'analyzing' | 'completed' | 'partial' | 'failed' | 'cancelled';
  progress: number;
  message: string | null;
}

export interface TrendStatistics {
  linear_regression: Record<string, number>;
  mann_kendall: Record<string, any>;
  sens_slope: Record<string, any>;
  descriptive_stats: Record<string, number>;
}

export interface TimeSeriesDataPoint {
  timestamp: string;
  value: number | null;
  anomaly: number | null;
}

export interface SpatialResult {
  grid_cell_id: string;
  lat: number;
  lon: number;
  trend_direction: 'increasing' | 'decreasing' | 'no_significant_trend' | 'insufficient_data';
  trend_magnitude: number | null;
  p_value: number | null;
  significance: boolean;
}

export interface InvestigationResults {
  investigation_id: string;
  status?: 'completed' | 'partial';
  region?: GeoJSONGeometry;
  time_range?: TimeRange;
  units?: Record<string, string>;
  insights?: string[];
  provenance?: Record<string, unknown>;
  dataset?: { id: string; provider: string; product_version: string };
  dataset_metadata: DatasetInfo[];
  variables: string[];
  time_series: Record<string, TimeSeriesDataPoint[]>;
  trend_statistics: Record<string, TrendStatistics>;
  spatial_results: Record<string, SpatialResult[]> | null;
  data_quality: Record<string, any>;
  methodology: string;
  limitations: string[];
  completed_at: string;
}

export interface InvestigationReport {
  title: string;
  investigation_id: string;
  region_description: string;
  variables: string[];
  dataset_info: DatasetInfo[];
  time_period: string;
  observation_count: Record<string, number>;
  units: Record<string, string>;
  data_quality_summary: string;
  trend_summary: Record<string, string>;
  rate_of_change: Record<string, number>;
  statistical_significance: Record<string, boolean>;
  confidence_intervals: Record<string, number[]>;
  temporal_chart_data: Record<string, TimeSeriesDataPoint[]>;
  spatial_visualization: string | null;
  interpretation: string;
  scientific_limitations: string[];
  data_source_citation: string;
  generated_at: string;
}

export interface AppState {
  // Investigation state
  investigation: {
    variables: string[];
    datasetId: string;
    geometry: GeoJSONGeometry | null;
    timeRange: TimeRange;
    temporalResolution: 'daily' | 'monthly' | 'annual' | 'seasonal';
  };
  // UI state
  ui: {
    activePanel: 'globe' | 'map' | 'results';
    sidebarOpen: boolean;
    loading: boolean;
    error: string | null;
  };
  // Data state
  data: {
    variables: VariableInfo[];
    currentInvestigation: InvestigationResults | null;
    currentReport: InvestigationReport | null;
    investigationStatus: InvestigationStatus | null;
  };
}
