"""Dataset registry mapping environmental variables to NASA Earth science products."""
from typing import Literal
from app.models.schemas import DatasetInfo, VariableInfo


# Environmental variable definitions
ENVIRONMENTAL_VARIABLES: dict[str, VariableInfo] = {
    "precipitation": VariableInfo(
        key="precipitation",
        display_name="Rainfall / Precipitation",
        description="Total precipitation rate including rain, snow, and other forms of water falling from the atmosphere",
        unit="mm/day",
        data_source="GPM IMERG Final Run V07 Monthly",
        available_coverage="2000-06 to present",
        spatial_resolution="0.1° × 0.1° (~11 km at equator)",
        scientific_explanation=(
            "Precipitation is the primary input of water to the land surface and a key component "
            "of the global water cycle. Changes in precipitation patterns can indicate shifts in "
            "climate systems, affect water resources, agriculture, and ecosystem health. GPM IMERG "
            "provides the most accurate global precipitation estimates by combining multiple "
            "satellite passive microwave and infrared observations with ground-based gauge data."
        ),
    ),
    "temperature": VariableInfo(
        key="temperature",
        display_name="Air Temperature",
        description="Near-surface air temperature at 2 meters above ground level",
        unit="°C",
        data_source="MERRA-2 Monthly Single-Level Diagnostics",
        available_coverage="1980-01 to present",
        spatial_resolution="0.5° × 0.625° (~50 km)",
        scientific_explanation=(
            "Air temperature is a fundamental climate variable that influences virtually all "
            "physical, chemical, and biological processes on Earth. MERRA-2 provides a "
            "reanalysis product that assimilates satellite and in-situ observations into a "
            "consistent atmospheric model, offering one of the best long-term records of "
            "near-surface temperature globally."
        ),
    ),
    "specific_humidity": VariableInfo(
        key="specific_humidity",
        display_name="Specific Humidity",
        description="Mass of water vapor per unit mass of moist air (kg/kg)",
        unit="kg/kg",
        data_source="MERRA-2 Monthly Single-Level Diagnostics",
        available_coverage="1980-01 to present",
        spatial_resolution="0.5° × 0.625° (~50 km)",
        scientific_explanation=(
            "Specific humidity measures the actual amount of water vapor in the air, "
            "independent of temperature. It is a more direct measure of atmospheric moisture "
            "content than relative humidity. Changes in specific humidity affect the Earth's "
            "radiation balance, precipitation formation, and human heat stress. MERRA-2 provides "
            "consistent long-term specific humidity records from its data assimilation system."
        ),
    ),
    "relative_humidity": VariableInfo(
        key="relative_humidity",
        display_name="Relative Humidity",
        description="Ratio of actual water vapor pressure to saturation vapor pressure (%)",
        unit="%",
        data_source="MERRA-2 Monthly Single-Level Diagnostics",
        available_coverage="1980-01 to present",
        spatial_resolution="0.5° × 0.625° (~50 km)",
        scientific_explanation=(
            "Relative humidity indicates how close the air is to saturation, directly affecting "
            "evaporation rates, cloud formation, and human comfort. It is temperature-dependent, "
            "so changes in relative humidity must be interpreted alongside temperature changes. "
            "MERRA-2 derives relative humidity from temperature and specific humidity fields."
        ),
    ),
    "soil_moisture": VariableInfo(
        key="soil_moisture",
        display_name="Soil Moisture",
        description="Volumetric water content in the top soil layer (0-10 cm)",
        unit="m³/m³",
        data_source="GLDAS Noah Land Surface Model V2.1",
        available_coverage="2000-01 to present",
        spatial_resolution="0.25° × 0.25° (~25 km)",
        scientific_explanation=(
            "Soil moisture controls the partitioning of precipitation into infiltration and "
            "runoff, regulates evapotranspiration, and is a key indicator of agricultural "
            "drought. GLDAS Noah model simulates soil moisture using observed meteorological "
            "forcing data, providing a consistent long-term record. The surface layer (0-10 cm) "
            "responds rapidly to precipitation and evaporation, making it sensitive to short-term "
            "weather variations and climate trends."
        ),
    ),
    "evapotranspiration": VariableInfo(
        key="evapotranspiration",
        display_name="Evapotranspiration",
        description="Total water vapor flux from land surface to atmosphere (evaporation + transpiration)",
        unit="mm/day",
        data_source="GLDAS Noah Land Surface Model V2.1",
        available_coverage="2000-01 to present",
        spatial_resolution="0.25° × 0.25° (~25 km)",
        scientific_explanation=(
            "Evapotranspiration (ET) is the sum of evaporation from soil and water surfaces "
            "and transpiration from plants. It represents the largest water flux from land to "
            "atmosphere after precipitation. ET links the water, energy, and carbon cycles. "
            "GLDAS Noah computes ET using the Penman-Monteith approach with model-simulated "
            "surface resistance and meteorological forcing. Changes in ET can indicate shifts in "
            "vegetation activity, water availability, or atmospheric demand."
        ),
    ),
    "runoff": VariableInfo(
        key="runoff",
        display_name="Surface Runoff",
        description="Water flow over the land surface that reaches stream channels",
        unit="mm/day",
        data_source="GLDAS Noah Land Surface Model V2.1",
        available_coverage="2000-01 to present",
        spatial_resolution="0.25° × 0.25° (~25 km)",
        scientific_explanation=(
            "Surface runoff is the portion of precipitation that flows overland to streams and "
            "rivers. It is a critical component of the water balance, determining streamflow "
            "and flood risk. GLDAS Noah simulates runoff using a conceptual bucket model with "
            "surface and subsurface flow components. Increasing runoff trends may indicate "
            "intensifying precipitation or decreasing infiltration capacity, while decreasing "
            "trends may suggest drier conditions or increased water abstraction."
        ),
    ),
    "subsurface_runoff": VariableInfo(
        key="subsurface_runoff",
        display_name="Subsurface Runoff (Baseflow)",
        description="Water flow through the subsurface that reaches stream channels",
        unit="mm/day",
        data_source="GLDAS Noah Land Surface Model V2.1",
        available_coverage="2000-01 to present",
        spatial_resolution="0.25° × 0.25° (~25 km)",
        scientific_explanation=(
            "Subsurface runoff (baseflow) represents groundwater contribution to streamflow. "
            "It sustains streams during dry periods and reflects aquifer recharge conditions. "
            "GLDAS Noah simulates baseflow using a linear reservoir model. Changes in baseflow "
            "trends can indicate long-term shifts in groundwater recharge, land use change, or "
            "climate-driven alterations to the hydrological cycle."
        ),
    ),
    "terrestrial_water_storage": VariableInfo(
        key="terrestrial_water_storage",
        display_name="Terrestrial Water Storage Anomaly",
        description="Total water storage anomaly including surface water, soil moisture, groundwater, and snow",
        unit="cm equivalent water height",
        data_source="GRACE/GRACE-FO Mascon Solutions",
        available_coverage="2002-04 to present (with 2017-2018 gap)",
        spatial_resolution="0.5° × 0.5° (~50 km)",
        scientific_explanation=(
            "Terrestrial Water Storage (TWS) anomalies from GRACE/GRACE-FO provide a unique "
            "integrated measure of all water storage changes: surface water, soil moisture, "
            "groundwater, and snow. Unlike other variables, TWS captures the total water budget "
            "change including deep groundwater that other datasets miss. The mascon solutions "
            "provide higher spatial resolution and reduced noise compared to spherical harmonic "
            "solutions. TWS trends reveal groundwater depletion, drought severity, and climate-"
            "driven water cycle changes."
        ),
    ),
    "ndvi": VariableInfo(
        key="ndvi",
        display_name="NDVI (Normalized Difference Vegetation Index)",
        description="Vegetation greenness index from satellite reflectance measurements",
        unit="Dimensionless (-1 to 1)",
        data_source="MODIS Terra/Aqua MOD13A2/MYD13A2 V6.1",
        available_coverage="2000-02 to present",
        spatial_resolution="1 km (16-day composite)",
        scientific_explanation=(
            "NDVI measures vegetation greenness and density by comparing near-infrared (which "
            "vegetation strongly reflects) and red (which vegetation absorbs) reflectance. "
            "Values range from -1 to 1, with higher values indicating healthier, denser "
            "vegetation. MODIS provides consistent 16-day composites at 1 km resolution. NDVI "
            "trends can reveal vegetation responses to climate change, land use change, "
            "CO₂ fertilization, and disturbance events like fire or drought."
        ),
    ),
    "evi": VariableInfo(
        key="evi",
        display_name="EVI (Enhanced Vegetation Index)",
        description="Improved vegetation index with reduced atmospheric and soil background effects",
        unit="Dimensionless (-1 to 1)",
        data_source="MODIS Terra/Aqua MOD13A2/MYD13A2 V6.1",
        available_coverage="2000-02 to present",
        spatial_resolution="1 km (16-day composite)",
        scientific_explanation=(
            "EVI improves upon NDVI by incorporating a blue band to correct for atmospheric "
            "aerosol effects and a canopy background adjustment factor. This makes EVI more "
            "sensitive to high-biomass regions like tropical forests and less sensitive to "
            "soil background variations. EVI is particularly valuable for monitoring dense "
            "vegetation where NDVI saturates. Both indices should be used together for robust "
            "vegetation trend analysis."
        ),
    ),
}


# NASA Dataset Registry - Maps variables to actual NASA products
DATASET_REGISTRY: dict[str, DatasetInfo] = {
    "gpm_imerg_monthly": DatasetInfo(
        feature_id="gpm_imerg_monthly",
        display_name="GPM IMERG Final Run V07 Monthly Precipitation",
        mission="GPM (Global Precipitation Measurement)",
        dataset_short_name="IMERG",
        collection_id="GPM_3IMERGM",
        version="V07",
        variable_name="precipitation",
        units="mm/hr (converted to mm/day)",
        spatial_resolution="0.1° × 0.1°",
        temporal_resolution="Monthly",
        historical_coverage="2000-06 to present",
        authentication_required=True,
        access_endpoint="https://gpm1.gesdisc.eosdis.nasa.gov/data/GPM_L3/GPM_3IMERGM.07/",
        processing_notes=(
            "Original unit is mm/hr; multiply by 24 for mm/day. "
            "Use 'precipitation' variable from NetCDF files. "
            "Final Run products have gauge calibration; Late and Early runs do not."
        ),
        description=(
            "IMERG (Integrated Multi-satellitE Retrievals for GPM) combines passive microwave "
            "and infrared observations from multiple satellites with ground-based gauge data "
            "to produce the best global precipitation estimates. The Final Run (monthly) includes "
            "gauge calibration and is the highest quality product for climate trend analysis."
        ),
    ),
    "merra2_temperature": DatasetInfo(
        feature_id="merra2_temperature",
        display_name="MERRA-2 Monthly 2m Air Temperature",
        mission="MERRA-2 (Modern-Era Retrospective analysis for Research and Applications, Version 2)",
        dataset_short_name="M2TMNXSLV",
        collection_id="M2TMNXSLV",
        version="5.12.4",
        variable_name="T2M",
        units="K (converted to °C)",
        spatial_resolution="0.5° × 0.625°",
        temporal_resolution="Monthly",
        historical_coverage="1980-01 to present",
        authentication_required=True,
        access_endpoint="https://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2TMNXSLV.5.12.4/",
        processing_notes=(
            "Original unit is Kelvin; subtract 273.15 for °C. "
            "Variable name in NetCDF: 'T2M'. "
            "Monthly mean of 3-hourly instantaneous values."
        ),
        description=(
            "MERRA-2 is NASA's latest atmospheric reanalysis, assimilating satellite and "
            "in-situ observations into the GEOS-5 model. The M2TMNXSLV collection provides "
            "monthly mean single-level diagnostics including 2-meter temperature (T2M), "
            "specific humidity (QV2M), and relative humidity (RH2M)."
        ),
    ),
    "merra2_specific_humidity": DatasetInfo(
        feature_id="merra2_specific_humidity",
        display_name="MERRA-2 Monthly 2m Specific Humidity",
        mission="MERRA-2",
        dataset_short_name="M2TMNXSLV",
        collection_id="M2TMNXSLV",
        version="5.12.4",
        variable_name="QV2M",
        units="kg/kg",
        spatial_resolution="0.5° × 0.625°",
        temporal_resolution="Monthly",
        historical_coverage="1980-01 to present",
        authentication_required=True,
        access_endpoint="https://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2TMNXSLV.5.12.4/",
        processing_notes=(
            "Variable name in NetCDF: 'QV2M'. "
            "Monthly mean of 3-hourly instantaneous values. "
            "This is specific humidity (mass of water vapor per mass of moist air)."
        ),
        description=(
            "Specific humidity from MERRA-2 reanalysis. Unlike relative humidity, specific "
            "humidity directly measures atmospheric moisture content independent of temperature."
        ),
    ),
    "merra2_relative_humidity": DatasetInfo(
        feature_id="merra2_relative_humidity",
        display_name="MERRA-2 Monthly 2m Relative Humidity",
        mission="MERRA-2",
        dataset_short_name="M2TMNXSLV",
        collection_id="M2TMNXSLV",
        version="5.12.4",
        variable_name="RH2M",
        units="%",
        spatial_resolution="0.5° × 0.625°",
        temporal_resolution="Monthly",
        historical_coverage="1980-01 to present",
        authentication_required=True,
        access_endpoint="https://goldsmr4.gesdisc.eosdis.nasa.gov/data/MERRA2/M2TMNXSLV.5.12.4/",
        processing_notes=(
            "Variable name in NetCDF: 'RH2M'. "
            "Monthly mean of 3-hourly instantaneous values. "
            "Derived from T2M and QV2M in the assimilation system."
        ),
        description=(
            "Relative humidity from MERRA-2 reanalysis. Temperature-dependent measure "
            "of atmospheric moisture saturation."
        ),
    ),
    "gldas_soil_moisture": DatasetInfo(
        feature_id="gldas_soil_moisture",
        display_name="GLDAS Noah V2.1 Surface Soil Moisture",
        mission="GLDAS (Global Land Data Assimilation System)",
        dataset_short_name="GLDAS_NOAH025_M",
        collection_id="GLDAS_NOAH025_M",
        version="V2.1",
        variable_name="SoilMoi0_10cm_inst",
        units="kg/m² (converted to m³/m³)",
        spatial_resolution="0.25° × 0.25°",
        temporal_resolution="Monthly",
        historical_coverage="2000-01 to present",
        authentication_required=True,
        access_endpoint="https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_M.2.1/",
        processing_notes=(
            "Variable: 'SoilMoi0_10cm_inst' (surface layer 0-10 cm). "
            "Original unit: kg/m² (mass per area). "
            "Convert to volumetric (m³/m³) by dividing by (1000 kg/m³ × 0.1 m) = 100. "
            "i.e., volumetric = kg/m² / 100."
        ),
        description=(
            "GLDAS Noah land surface model forced with observation-based meteorological data. "
            "Provides consistent long-term soil moisture simulations. The surface layer (0-10 cm) "
            "responds rapidly to precipitation and evaporation events."
        ),
    ),
    "gldas_evapotranspiration": DatasetInfo(
        feature_id="gldas_evapotranspiration",
        display_name="GLDAS Noah V2.1 Evapotranspiration",
        mission="GLDAS",
        dataset_short_name="GLDAS_NOAH025_M",
        collection_id="GLDAS_NOAH025_M",
        version="V2.1",
        variable_name="Evap_tavg",
        units="W/m² (converted to mm/day)",
        spatial_resolution="0.25° × 0.25°",
        temporal_resolution="Monthly",
        historical_coverage="2000-01 to present",
        authentication_required=True,
        access_endpoint="https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_M.2.1/",
        processing_notes=(
            "Variable: 'Evap_tavg' (average latent heat flux in W/m²). "
            "Convert to mm/day: mm/day = (W/m² × 86400 s/day) / (2.501 × 10⁶ J/kg × 1000 kg/m³) "
            "≈ W/m² × 0.0345. "
            "Latent heat of vaporization ≈ 2.501 MJ/kg at 20°C."
        ),
        description=(
            "Total evapotranspiration from GLDAS Noah model including soil evaporation and "
            "plant transpiration. Computed using Penman-Monteith approach with model-simulated "
            "surface resistance."
        ),
    ),
    "gldas_runoff": DatasetInfo(
        feature_id="gldas_runoff",
        display_name="GLDAS Noah V2.1 Surface Runoff",
        mission="GLDAS",
        dataset_short_name="GLDAS_NOAH025_M",
        collection_id="GLDAS_NOAH025_M",
        version="V2.1",
        variable_name="Qs_tavg",
        units="kg/m²/s (converted to mm/day)",
        spatial_resolution="0.25° × 0.25°",
        temporal_resolution="Monthly",
        historical_coverage="2000-01 to present",
        authentication_required=True,
        access_endpoint="https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_M.2.1/",
        processing_notes=(
            "Variable: 'Qs_tavg' (surface runoff in kg/m²/s). "
            "Convert to mm/day: 1 kg/m²/s = 86400 mm/day (since 1 kg/m² = 1 mm water)."
        ),
        description=(
            "Surface runoff from GLDAS Noah model. Represents overland flow reaching stream channels."
        ),
    ),
    "gldas_subsurface_runoff": DatasetInfo(
        feature_id="gldas_subsurface_runoff",
        display_name="GLDAS Noah V2.1 Subsurface Runoff (Baseflow)",
        mission="GLDAS",
        dataset_short_name="GLDAS_NOAH025_M",
        collection_id="GLDAS_NOAH025_M",
        version="V2.1",
        variable_name="Qsb_tavg",
        units="kg/m²/s (converted to mm/day)",
        spatial_resolution="0.25° × 0.25°",
        temporal_resolution="Monthly",
        historical_coverage="2000-01 to present",
        authentication_required=True,
        access_endpoint="https://hydro1.gesdisc.eosdis.nasa.gov/data/GLDAS/GLDAS_NOAH025_M.2.1/",
        processing_notes=(
            "Variable: 'Qsb_tavg' (subsurface runoff/baseflow in kg/m²/s). "
            "Convert to mm/day: 1 kg/m²/s = 86400 mm/day."
        ),
        description=(
            "Subsurface runoff (baseflow) from GLDAS Noah model. Represents groundwater "
            "contribution to streamflow."
        ),
    ),
}


def get_variable_info(key: str) -> VariableInfo | None:
    """Get variable information by key."""
    return ENVIRONMENTAL_VARIABLES.get(key)


def get_dataset_info(dataset_id: str) -> DatasetInfo | None:
    """Get dataset information by dataset ID."""
    return DATASET_REGISTRY.get(dataset_id)


def get_dataset_for_variable(variable: str) -> DatasetInfo | None:
    """Map environmental variable to its primary dataset."""
    mapping = {
        "precipitation": "gpm_imerg_monthly",
        "temperature": "merra2_temperature",
        "specific_humidity": "merra2_specific_humidity",
        "relative_humidity": "merra2_relative_humidity",
        "soil_moisture": "gldas_soil_moisture",
        "evapotranspiration": "gldas_evapotranspiration",
        "runoff": "gldas_runoff",
        "subsurface_runoff": "gldas_subsurface_runoff",
    }
    dataset_id = mapping.get(variable)
    if dataset_id:
        return DATASET_REGISTRY.get(dataset_id)
    return None


def list_available_variables() -> list[VariableInfo]:
    """List all available environmental variables."""
    return list(ENVIRONMENTAL_VARIABLES.values())


def list_available_datasets() -> list[DatasetInfo]:
    """List all available datasets."""
    return list(DATASET_REGISTRY.values())