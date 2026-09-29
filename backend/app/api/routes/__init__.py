from fastapi import APIRouter
from .health import router as health_router
from .stations import router as stations_router
from .telemetry_ingest import router as telemetry_ingest_router
from .alerts import router as alerts_router
from .auth import router as auth_router
from .simulation import router as simulation_router
from .recommendations import router as recommendations_router
from .intelligence import router as intelligence_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["Health"])
api_router.include_router(stations_router, tags=["Stations & Digital Twin"])
api_router.include_router(telemetry_ingest_router, prefix="/telemetry", tags=["Telemetry Ingestion"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(simulation_router, prefix="/simulation", tags=["Simulation"])
api_router.include_router(recommendations_router, prefix="/recommendations", tags=["Recommendations"])
api_router.include_router(intelligence_router, prefix="/intelligence", tags=["AI / Risk / Simulation Intelligence"])
