"""Variable descriptions for capabilities currently backed by acquisition."""
from app.models.schemas import VariableInfo

ENVIRONMENTAL_VARIABLES: dict[str, VariableInfo] = {
    "precipitation": VariableInfo(
        key="precipitation",
        display_name="Rainfall / Precipitation",
        description="Monthly GPM IMERG precipitation estimate. The original measurement unit is read from each granule and preserved.",
        unit="mm/hr (monthly mean rate)",
        data_source="GPM IMERG Final Precipitation L3 Monthly V07",
        available_coverage="2000-06 to 2025-09 in the currently available V07B archive",
        spatial_resolution="0.1° × 0.1°",
        scientific_explanation=("Regional monthly precipitation estimates are spatially averaged using grid-cell overlap and spherical area weights. Trend estimates describe the selected record; they do not establish a cause."),
        dataset_ids=["gpm_imerg_monthly", "noaa_ghcn_monthly_precipitation"],
    )
}

def get_variable_info(key: str) -> VariableInfo | None:
    return ENVIRONMENTAL_VARIABLES.get(key)

def list_available_variables() -> list[VariableInfo]:
    return list(ENVIRONMENTAL_VARIABLES.values())
