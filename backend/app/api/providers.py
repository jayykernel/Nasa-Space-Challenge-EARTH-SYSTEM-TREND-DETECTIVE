from fastapi import APIRouter
from app.models.schemas import ProviderInfo

router=APIRouter(tags=["providers"])

@router.get("/providers",response_model=list[ProviderInfo])
async def providers():
    return [
        ProviderInfo(id="earthdata",name="NASA Earthdata / GPM IMERG",status="implemented",details="CMR granule discovery and Earthaccess download; Earthdata Login credentials are required for protected data."),
        ProviderInfo(id="appeears",name="NASA AppEEARS",status="not_implemented",details="No verified task submission pipeline is enabled in this release."),
        ProviderInfo(id="giovanni",name="NASA Giovanni",status="not_implemented",details="No documented programmatic analysis workflow is enabled in this release."),
        ProviderInfo(id="hydrology",name="NASA Hydrology Time Series",status="not_implemented",details="A supported programmatic endpoint has not been established; no connector is claimed."),
        ProviderInfo(id="noaa",name="NOAA Climate Data Online",status="implemented",details="NOAA CDO v2 GSOM monthly precipitation station discovery and retrieval; NOAA_CDO_TOKEN required. Results are station averages, not gridded fields."),
    ]
