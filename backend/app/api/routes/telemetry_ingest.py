from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.schemas import SuccessResponse, ErrorResponse
from app.schemas.telemetry import TelemetryOut, TelemetryBase
from app.services.telemetry_service import ingest_telemetry
from app.api.dependencies import get_db

router = APIRouter(tags=["Telemetry Ingestion"])

@router.post("/ingest", response_model=SuccessResponse)
def ingest_endpoint(payload: TelemetryBase, db: Session = Depends(get_db)):
    """Internal testing endpoint – uses the same service as MQTT ingestion."""
    try:
        telemetry = ingest_telemetry(payload.model_dump() if hasattr(payload, "model_dump") else payload.dict(), db)
    except HTTPException as exc:
        raise exc
    telemetry_data = {
        "id": telemetry.id,
        "sensor_id": telemetry.sensor_id,
        "value": telemetry.value,
        "quality": telemetry.quality,
        "source": telemetry.source,
        "timestamp": telemetry.timestamp.isoformat() if telemetry.timestamp else None,
    }
    return SuccessResponse(data=telemetry_data)
