# Rule-Based Alert Engine Specification

## 1. Overview
The POLAR-TWIN Alert Engine continuously evaluates ingested telemetry against centralized, configurable environmental and operational thresholds. It ensures fast, deterministic alerting for life-critical Antarctic conditions without depending on heavy ML inference.

---

## 2. Configurable Alert Thresholds

Thresholds are centralized in application configuration (`app/core/config.py`) and overridable via `.env`:

| Parameter | Default | Severity | Condition / Trigger |
|---|---|---|---|
| `ALERT_FUEL_CRITICAL_THRESHOLD` | `20.0 %` | `CRITICAL` | Fuel reserve drops below 20% |
| `ALERT_FUEL_EMERGENCY_THRESHOLD` | `10.0 %` | `CRITICAL` | Fuel reserve drops below 10% (Immediate resupply emergency) |
| `ALERT_TEMP_SAFE_MIN_THRESHOLD` | `-50.0 °C` | `WARNING` | Outside temperature plunges below safe operational envelope |
| `ALERT_WIND_MAX_THRESHOLD` | `40.0 m/s` | `CRITICAL` | Blizzard storm velocity exceeds 40 m/s (~144 km/h) |
| `ALERT_GENERATOR_LOAD_MAX_THRESHOLD` | `95.0 %` | `WARNING` | Continuous diesel generator load exceeds 95% |
| Equipment Status = `FAILED` | N/A | `CRITICAL` | Critical life support or power equipment failure |
| Sensor Status = `DISCONNECTED` | N/A | `WARNING` | Edge sensor lost communication or faulty |

---

## 3. Alert Deduplication & Auto-Resolution

- **Deduplication**: When an alert condition persists, duplicate alerts are suppressed. The existing active alert is refreshed rather than flooding station operators.
- **Auto-Resolution**: When telemetry values return to the safe operating window, active alerts are automatically transitioned to `RESOLVED` status with a resolution timestamp.

---

## 4. Endpoints

### 4.1 List Station Alerts
`GET /api/alerts/{station_id}?status=active`

Retrieve active, acknowledged, or resolved alerts for a given station.

### 4.2 Acknowledge Alert
`POST /api/alerts/{alert_id}/ack`

Station controllers acknowledge awareness of an active alert condition.

### 4.3 Resolve Alert
`POST /api/alerts/{alert_id}/resolve`

Manually marks an alert as resolved with controller notes.
