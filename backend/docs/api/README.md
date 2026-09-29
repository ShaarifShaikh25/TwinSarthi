# POLAR-TWIN Backend REST & WebSocket API Documentation

## 1. Overview
**POLAR-TWIN** is a Predictive & Causal Digital Twin platform engineered for India's Antarctic research stations:
- **Maitri** (70°45′58″S, 11°44′09″E, Schirmacher Oasis)
- **Bharati** (69°24′29″S, 76°11′14″E, Larsemann Hills)

The backend provides high-throughput telemetry ingestion, deterministic real-time digital twin state aggregation, an automated rule-based alert engine, JWT-secured role-based access control (RBAC), and clean extension interfaces for AI/Risk/Simulation algorithms (developed by Developer 3).

---

## 2. Base URLs & Standards

- **REST API Base URL**: `http://localhost:8000/api`
- **Interactive OpenAPI Documentation**: `http://localhost:8000/api/docs`
- **Alternative ReDoc Documentation**: `http://localhost:8000/api/redoc`
- **WebSocket Gateway**: `ws://localhost:8000/ws/{station_id}`
- **Liveness Probe**: `GET http://localhost:8000/health`

### Standard Response Envelope
All REST API endpoints return JSON conforming to standard response envelopes:

#### Success Envelope (`HTTP 200 / 201`):
```json
{
  "success": true,
  "data": { ... }
}
```

#### Error Envelope (`HTTP 4xx / 5xx`):
```json
{
  "success": false,
  "error": {
    "code": "BAD_REQUEST",
    "message": "Detailed description of error",
    "details": null
  }
}
```

---

## 3. Documentation Index

| Topic | Document | Description |
|---|---|---|
| **Authentication & RBAC** | [`auth.md`](./auth.md) | JWT token creation, `/api/auth/me`, Admin/Controller/Viewer permissions |
| **Stations & Digital Twin** | [`stations_and_twin.md`](./stations_and_twin.md) | Station registry, equipment, sensors, inventory, and twin state aggregation |
| **Telemetry Ingestion** | [`telemetry.md`](./telemetry.md) | Ingestion pipeline, payload structure, data source honesty |
| **Rule-Based Alerts** | [`alerts.md`](./alerts.md) | Thresholds, deduplication, auto-resolution, active/ack/resolved lifecycle |
| **AI, Risk & Simulation** | [`intelligence_and_simulation.md`](./intelligence_and_simulation.md) | Clean interfaces for Developer 3 (Energy, Fuel, Anomaly, Risk, What-If, Resupply) |
| **Recommendations** | [`recommendations.md`](./recommendations.md) | Human-in-the-loop decision interface (approve, modify, reject) and audit logs |
| **WebSocket Protocol** | [`websocket.md`](./websocket.md) | Real-time channel `/ws/{station_id}` with 6 streaming event types |
