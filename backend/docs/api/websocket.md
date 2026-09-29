# WebSocket Real-Time Event Protocol Specification

## 1. Connection Endpoint
`ws://<host>:8000/ws/{station_id}`

Clients (Frontend dashboards, edge telemetry monitors) connect using the lowercase or uppercase station identifier:
- `ws://localhost:8000/ws/maitri`
- `ws://localhost:8000/ws/bharati`

---

## 2. Event Types & Payloads

The WebSocket server broadcasts 6 standardized event types:

### 2.1 `telemetry_update`
Broadcast whenever new valid telemetry is ingested.
```json
{
  "type": "telemetry_update",
  "station_id": "maitri",
  "sensor": "Ambient Temperature",
  "sensor_id": 1,
  "sensor_type": "temperature",
  "value": -24.5,
  "timestamp": "2026-09-29T12:00:00Z",
  "quality": "GOOD",
  "source": "SIMULATED"
}
```

---

### 2.2 `equipment_update`
Broadcast when equipment health, operational mode, or status changes.
```json
{
  "type": "equipment_update",
  "station_id": "maitri",
  "equipment_id": 1,
  "equipment_name": "Diesel Generator 1",
  "status": "operational",
  "health_score": 96.5,
  "timestamp": "2026-09-29T12:00:00Z"
}
```

---

### 2.3 `alert`
Broadcast immediately upon alert triggering, acknowledgment, or resolution.
```json
{
  "type": "alert",
  "station_id": "maitri",
  "alert": {
    "id": 12,
    "severity": "CRITICAL",
    "status": "ACTIVE",
    "message": "Critical fuel reserve level: 18.5% is below safety threshold 20.0%",
    "created_at": "2026-09-29T12:00:00Z"
  }
}
```

---

### 2.4 `digital_twin_update`
Broadcast whenever the unified digital twin state is refreshed by new telemetry.
```json
{
  "type": "digital_twin_update",
  "station_id": "maitri",
  "timestamp": "2026-09-29T12:00:00Z",
  "data": {
    "status": "active",
    "environment": { "temperature": -24.5, "wind_speed": 18.2 },
    "energy": { "total_load_kw": 88.0, "fuel_percentage": 71.0 },
    "equipment": { "status": "operational", "health_score": 96.5 },
    "logistics": { "fuel_days_remaining": 118.3 }
  }
}
```

---

### 2.5 `risk_update`
Broadcast when cascading risk levels change.
```json
{
  "type": "risk_update",
  "station_id": "maitri",
  "risk_level": "HIGH",
  "active_alerts_count": 2,
  "timestamp": "2026-09-29T12:00:00Z"
}
```

---

### 2.6 `recommendation`
Broadcast when new actionable decision recommendations are issued.
```json
{
  "type": "recommendation",
  "station_id": "maitri",
  "recommendations": [
    "Inspect Diesel Generator 1 immediately due to high vibration"
  ],
  "timestamp": "2026-09-29T12:00:00Z"
}
```
