"""Public variable metadata and the subset backed by verified pipelines."""
from app.registry.datasets import ENVIRONMENTAL_VARIABLES

SUPPORTED_VARIABLES = {"precipitation": ["gpm_imerg_monthly", "noaa_ghcn_monthly_precipitation"]}

def list_variables():
    return list(ENVIRONMENTAL_VARIABLES.values())

def get_variable(key: str):
    return ENVIRONMENTAL_VARIABLES.get(key)
