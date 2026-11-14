import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  AppState,
  VariableInfo,
  InvestigationRequest,
  InvestigationResults,
  InvestigationReport,
  InvestigationStatus,
  GeoJSONGeometry,
  TimeRange,
} from '../types';

interface StoreState extends AppState {
  // Actions
  setVariables: (variables: string[]) => void;
  setGeometry: (geometry: GeoJSONGeometry | null) => void;
  setTimeRange: (timeRange: TimeRange) => void;
  setTemporalResolution: (resolution: 'daily' | 'monthly' | 'annual' | 'seasonal') => void;
  setActivePanel: (panel: 'globe' | 'map' | 'results') => void;
  setSidebarOpen: (open: boolean) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setAvailableVariables: (variables: VariableInfo[]) => void;
  setInvestigationResults: (results: InvestigationResults | null) => void;
  setInvestigationReport: (report: InvestigationReport | null) => void;
  setInvestigationStatus: (status: InvestigationStatus | null) => void;
  resetInvestigation: () => void;
  // Investigation request builder
  buildInvestigationRequest: () => InvestigationRequest | null;
}

const initialState: AppState = {
  investigation: {
    variables: [],
    geometry: null,
    timeRange: { start: '2000-01-01', end: '2025-12-31' },
    temporalResolution: 'monthly',
  },
  ui: {
    activePanel: 'globe',
    sidebarOpen: true,
    loading: false,
    error: null,
  },
  data: {
    variables: [],
    currentInvestigation: null,
    currentReport: null,
    investigationStatus: null,
  },
};

export const useStore = create<StoreState>()(
  persist(
    (set, get) => ({
      ...initialState,

      setVariables: (variables) =>
        set((state) => ({
          investigation: { ...state.investigation, variables },
        })),

      setGeometry: (geometry) =>
        set((state) => ({
          investigation: { ...state.investigation, geometry },
        })),

      setTimeRange: (timeRange) =>
        set((state) => ({
          investigation: { ...state.investigation, timeRange },
        })),

      setTemporalResolution: (temporalResolution) =>
        set((state) => ({
          investigation: { ...state.investigation, temporalResolution },
        })),

      setActivePanel: (activePanel) =>
        set((state) => ({
          ui: { ...state.ui, activePanel },
        })),

      setSidebarOpen: (sidebarOpen) =>
        set((state) => ({
          ui: { ...state.ui, sidebarOpen },
        })),

      setLoading: (loading) =>
        set((state) => ({
          ui: { ...state.ui, loading },
        })),

      setError: (error) =>
        set((state) => ({
          ui: { ...state.ui, error },
        })),

      setAvailableVariables: (variables) =>
        set((state) => ({
          data: { ...state.data, variables },
        })),

      setInvestigationResults: (currentInvestigation) =>
        set((state) => ({
          data: { ...state.data, currentInvestigation },
        })),

      setInvestigationReport: (currentReport) =>
        set((state) => ({
          data: { ...state.data, currentReport },
        })),

      setInvestigationStatus: (investigationStatus) =>
        set((state) => ({
          data: { ...state.data, investigationStatus },
        })),

      resetInvestigation: () =>
        set((state) => ({
          investigation: initialState.investigation,
          data: {
            ...state.data,
            currentInvestigation: null,
            currentReport: null,
            investigationStatus: null,
          },
        })),

      buildInvestigationRequest: () => {
        const { investigation } = get();
        if (!investigation.geometry || investigation.variables.length === 0) {
          return null;
        }
        return {
          variables: investigation.variables,
          geometry: investigation.geometry,
          time_range: investigation.timeRange,
          temporal_resolution: investigation.temporalResolution,
        };
      },
    }),
    {
      name: 'earth-trend-detective-store',
      partialize: (state) => ({
        investigation: state.investigation,
        ui: { sidebarOpen: state.ui.sidebarOpen },
      }),
    }
  )
);