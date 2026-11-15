/** API service for communicating with the backend */

const configuredApiOrigin = import.meta.env.VITE_API_BASE_URL?.replace(/\/+$/, '');
const API_BASE = `${configuredApiOrigin || 'https://earth-system-trend-api.onrender.com'}/api/v1`;

export interface InvestigationRequest {
  variables: string[];
  dataset_id?: string;
  provider?: string;
  geometry: GeoJSONGeometry;
  time_range: { start: string; end: string };
  temporal_resolution: 'daily' | 'monthly' | 'annual' | 'seasonal';
}

export interface GeoJSONGeometry {
  type: 'Point' | 'Polygon' | 'MultiPolygon' | 'Feature' | 'FeatureCollection';
  coordinates?: any;
  geometry?: any;
  properties?: any;
  features?: any;
}

export interface InvestigationResponse {
  investigation_id: string;
  status: string;
  message: string;
}

export interface InvestigationStatus {
  investigation_id: string;
  status: 'queued' | 'retrieving_data' | 'validating' | 'normalizing' | 'processing' | 'analyzing' | 'completed' | 'partial' | 'failed' | 'cancelled';
  progress: number;
  message: string | null;
}

export interface InvestigationResults {
  investigation_id: string;
  dataset_metadata: DatasetInfo[];
  status?: 'completed' | 'partial';
  region?: GeoJSONGeometry;
  time_range?: { start: string; end: string };
  units?: Record<string, string>;
  insights?: string[];
  provenance?: Record<string, unknown>;
  dataset?: { id: string; provider: string; product_version: string };
  variables: string[];
  time_series: Record<string, any[]>;
  trend_statistics: Record<string, any>;
  spatial_results: Record<string, any[]> | null;
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
  dataset_info: any[];
  time_period: string;
  observation_count: Record<string, number>;
  units: Record<string, string>;
  data_quality_summary: string;
  trend_summary: Record<string, string>;
  rate_of_change: Record<string, number>;
  statistical_significance: Record<string, boolean>;
  confidence_intervals: Record<string, number[]>;
  temporal_chart_data: Record<string, any[]>;
  spatial_visualization: string | null;
  interpretation: string;
  scientific_limitations: string[];
  data_source_citation: string;
  generated_at: string;
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
}

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'The server returned an unreadable response.' }));
      const detail = error?.detail;
      const message = Array.isArray(detail)
        ? detail.map((item: unknown) => {
            if (typeof item === 'string') return item;
            if (item && typeof item === 'object' && 'msg' in item) {
              const issue = item as { msg: string; loc?: Array<string | number> };
              const location = issue.loc?.filter((part) => part !== 'body').join(' → ');
              return location ? `${location}: ${issue.msg}` : issue.msg;
            }
            return JSON.stringify(item);
          }).join('; ')
        : typeof detail === 'string'
          ? detail
          : detail && typeof detail === 'object'
            ? JSON.stringify(detail)
            : `Request failed (HTTP ${response.status})`;
      throw new Error(message);
    }

    return response.json();
  }

  // Variables
  async getVariables(): Promise<VariableInfo[]> {
    return this.request<VariableInfo[]>('/variables');
  }

  async getVariable(key: string): Promise<VariableInfo> {
    return this.request<VariableInfo>(`/variables/${key}`);
  }

  // Datasets
  async getDatasets(): Promise<DatasetInfo[]> {
    return this.request<DatasetInfo[]>('/datasets');
  }

  // Investigations
  async startInvestigation(request: InvestigationRequest): Promise<InvestigationResponse> {
    return this.request<InvestigationResponse>('/analysis', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getInvestigationStatus(id: string): Promise<InvestigationStatus> {
    return this.request<InvestigationStatus>(`/analysis/${id}/status`);
  }

  async getInvestigationResults(id: string): Promise<InvestigationResults> {
    return this.request<InvestigationResults>(`/analysis/${id}/results`);
  }

  async getInvestigationMap(id: string): Promise<any> {
    return this.request<any>(`/analysis/${id}/map`);
  }

  async getInvestigationReport(id: string): Promise<InvestigationReport> {
    return this.request<InvestigationReport>(`/analysis/${id}/report`);
  }

  async cancelInvestigation(id: string): Promise<{ investigation_id: string; status: string; message: string }> {
    return this.request(`/analysis/${id}/cancel`, { method: 'POST' });
  }

  // Polling helper
  async pollInvestigation(
    investigationId: string,
    onProgress: (status: InvestigationStatus) => void,
    maxAttempts = 3600,
    intervalMs = 2000
  ): Promise<InvestigationResults> {
    for (let attempt = 0; attempt < maxAttempts; attempt++) {
      const status = await this.getInvestigationStatus(investigationId);
      onProgress(status);

      if (status.status === 'completed' || status.status === 'partial') {
        return this.getInvestigationResults(investigationId);
      }

      if (status.status === 'failed') {
        throw new Error(status.message || 'Investigation failed');
      }

      if (status.status === 'cancelled') {
        throw new Error('Investigation cancelled');
      }

      await new Promise(resolve => setTimeout(resolve, intervalMs));
    }

    throw new Error('Investigation timed out');
  }
}

export const api = new ApiService();
