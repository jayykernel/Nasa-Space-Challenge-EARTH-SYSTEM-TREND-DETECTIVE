"""Pydantic models for API request/response schemas."""
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


class Geometry(BaseModel):
    """GeoJSON geometry object."""
    type: Literal["Point", "Polygon", "MultiPolygon", "Feature", "FeatureCollection"]
    coordinates: Any = None
    geometry: Any = None
    properties: Any = None
    features: Any = None


class TimeRange(BaseModel):
    """Temporal range for investigation."""
    start: str = Field(..., description="Start date in YYYY-MM-DD format")
    end: str = Field(..., description="End date in YYYY-MM-DD format")


class InvestigationRequest(BaseModel):
    """Request to start an investigation."""
    variables: list[str] = Field(..., min_length=1, description="Environmental variables to investigate")
    geometry: Geometry = Field(..., description="Geographical region as GeoJSON")
    time_range: TimeRange
    temporal_resolution: Literal["daily", "monthly", "annual", "seasonal"] = "monthly"


class DatasetInfo(BaseModel):
    """Information about a NASA dataset."""
    feature_id: str
    display_name: str
    mission: str
    dataset_short_name: str
    collection_id: str
    version: str
    variable_name: str
    units: str
    spatial_resolution: str
    temporal_resolution: str
    historical_coverage: str
    authentication_required: bool
    access_endpoint: str
    processing_notes: str | None = None
    description: str


class VariableInfo(BaseModel):
    """Environmental variable information."""
    key: str
    display_name: str
    description: str
    unit: str
    data_source: str
    available_coverage: str
    spatial_resolution: str
    scientific_explanation: str


class InvestigationStatus(BaseModel):
    """Investigation job status."""
    id: str
    status: Literal["queued", "retrieving_data", "processing", "analyzing", "completed", "failed", "cancelled"]
    progress: int = Field(ge=0, le=100, default=0)
    message: str | None = None
    created_at: datetime
    updated_at: datetime


class TrendStatistics(BaseModel):
    """Statistical trend analysis results."""
    linear_regression: dict[str, float] = Field(default_factory=dict)
    mann_kendall: dict[str, Any] = Field(default_factory=dict)
    sens_slope: dict[str, Any] = Field(default_factory=dict)
    descriptive_stats: dict[str, float] = Field(default_factory=dict)


class TimeSeriesData(BaseModel):
    """Time series data point."""
    timestamp: str
    value: float | None
    anomaly: float | None = None


class SpatialResult(BaseModel):
    """Spatial trend analysis result."""
    grid_cell_id: str
    lat: float
    lon: float
    trend_direction: Literal["increasing", "decreasing", "no_significant_trend", "insufficient_data"]
    trend_magnitude: float | None
    p_value: float | None
    significance: bool


class InvestigationResults(BaseModel):
    """Complete investigation results."""
    investigation_id: str
    dataset_metadata: list[DatasetInfo]
    variables: list[str]
    time_series: dict[str, list[TimeSeriesData]]
    trend_statistics: dict[str, TrendStatistics]
    spatial_results: dict[str, list[SpatialResult]] | None = None
    data_quality: dict[str, Any] = Field(default_factory=dict)
    methodology: str
    limitations: list[str] = Field(default_factory=list)
    completed_at: datetime


class InvestigationReport(BaseModel):
    """Scientific investigation report."""
    title: str
    investigation_id: str
    region_description: str
    variables: list[str]
    dataset_info: list[DatasetInfo]
    time_period: str
    observation_count: dict[str, int]
    units: dict[str, str]
    data_quality_summary: str
    trend_summary: dict[str, str]
    rate_of_change: dict[str, float]
    statistical_significance: dict[str, bool]
    confidence_intervals: dict[str, list[float]]
    temporal_chart_data: dict[str, list[TimeSeriesData]]
    spatial_visualization: str | None = None
    interpretation: str
    scientific_limitations: list[str]
    data_source_citation: str
    generated_at: datetime