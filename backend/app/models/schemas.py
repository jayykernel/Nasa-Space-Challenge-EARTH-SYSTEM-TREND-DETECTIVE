"""Validated, provider-independent API and pipeline models."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class TimeRange(BaseModel):
    start: date
    end: date

    @model_validator(mode="after")
    def ordered(self):
        if self.end < self.start:
            raise ValueError("time_range.end must be on or after time_range.start")
        return self


class AnalysisConfig(BaseModel):
    alpha: float = Field(default=0.05, gt=0, lt=1)
    seasonal_period: int = Field(default=12, ge=2, le=366)


class InvestigationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    variable: str | None = None
    variables: list[str] = Field(default_factory=list, min_length=0)
    geometry: dict[str, Any]
    time_range: TimeRange
    temporal_resolution: Literal["daily", "monthly", "annual", "seasonal"] = "monthly"
    dataset_id: str | None = None
    provider: str | None = None
    analysis: AnalysisConfig = Field(default_factory=AnalysisConfig)

    @field_validator("geometry")
    @classmethod
    def valid_geometry(cls, value):
        from shapely.geometry import shape
        from shapely.validation import explain_validity

        geo = value.get("geometry") if value.get("type") == "Feature" else value
        if not isinstance(geo, dict) or geo.get("type") not in ("Polygon", "MultiPolygon"):
            raise ValueError("geometry must be a GeoJSON Polygon or MultiPolygon")
        try:
            parsed = shape(geo)
        except Exception as exc:
            raise ValueError(f"Invalid GeoJSON geometry: {exc}") from exc
        if parsed.is_empty or not parsed.is_valid or parsed.area <= 0:
            raise ValueError(f"Invalid geometry: {explain_validity(parsed)}")
        minx, miny, maxx, maxy = parsed.bounds
        if minx < -180 or maxx > 180 or miny < -90 or maxy > 90:
            raise ValueError("Geometry coordinates must use WGS84 longitude/latitude")
        return geo

    @model_validator(mode="after")
    def resolve_variables(self):
        selected = list(dict.fromkeys(self.variables + ([self.variable] if self.variable else [])))
        if not selected:
            raise ValueError("Provide variable or variables")
        if len(selected) != 1:
            raise ValueError("This acquisition workflow currently accepts one variable per investigation")
        self.variable = selected[0]
        self.variables = selected
        return self


class AcquisitionResult(BaseModel):
    investigation_id: str
    provider: str
    dataset_id: str
    product_version: str | None = None
    status: Literal["completed", "partial", "failed"]
    raw_files: list[str] = Field(default_factory=list)
    raw_format: str
    requested_variable: str
    requested_time_range: TimeRange
    requested_geometry: dict[str, Any] | None = None
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    acquisition_metadata: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)


class InvestigationStatusResponse(BaseModel):
    investigation_id: str
    status: Literal["queued", "retrieving_data", "validating", "normalizing", "processing", "analyzing", "completed", "partial", "failed", "cancelled"]
    progress: int = Field(ge=0, le=100)
    message: str | None = None
    created_at: datetime
    updated_at: datetime


class DatasetInfo(BaseModel):
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
    acquisition_status: str = "available"


class VariableInfo(BaseModel):
    key: str
    display_name: str
    description: str
    unit: str
    data_source: str
    available_coverage: str
    spatial_resolution: str
    scientific_explanation: str
    dataset_ids: list[str] = Field(default_factory=list)


class ProviderInfo(BaseModel):
    id: str
    name: str
    status: str
    details: str


class ApiError(BaseModel):
    detail: str

class InvestigationCreatedResponse(BaseModel):
    investigation_id: str
    status: str
    message: str

class InvestigationResultsResponse(BaseModel):
    investigation_id: str
    status: Literal["completed", "partial"]
    variable: str
    variables: list[str]
    dataset_metadata: list[dict[str, Any]]
    dataset: dict[str, Any]
    region: dict[str, Any]
    time_range: dict[str, str]
    temporal_resolution: str
    time_series: dict[str, list[dict[str, Any]]]
    trend_statistics: dict[str, Any]
    spatial_results: dict[str, Any]
    units: dict[str, str]
    data_quality: dict[str, Any]
    methodology: str
    limitations: list[str]
    insights: list[str]
    completed_at: datetime
    processed_files: dict[str, str]
    provenance: dict[str, Any]
    report: dict[str, Any]
