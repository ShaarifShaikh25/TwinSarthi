# Stations, Infrastructure & Digital Twin State API

## 1. Overview
The Antarctic stations (`MAITRI` and `BHARATI`) represent real physical sites. The **Digital Twin** provides an aggregated, multi-domain digital reflection of station telemetry, equipment status, energy microgrids, and logistics stock.

---

## 2. Endpoints

### 2.1 List Stations
`GET /api/stations`

Returns all registered Antarctic research stations.

#### Response (`HTTP 200`)
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "Maitri Research Station",
      "code": "MAITRI",
      "latitude": -70.7667,
      "longitude": 11.7333,
      "status": "active",
      "created_at": "2026-09-29T10:00:00Z"
    },
    {
      "id": 2,
      "name": "Bharati Research Station",
      "code": "BHARATI",
      "latitude": -69.4072,
      "longitude": 76.1872,
      "status": "active",
      "created_at": "2026-09-29T10:00:00Z"
    }
  ]
}
```

---

### 2.2 Get Station Details
`GET /api/stations/{station_id}`

Retrieve station details by ID (e.g. `1`) or code (`MAITRI` / `BHARATI`).

---

### 2.3 Get Infrastructure & Equipment
`GET /api/infrastructure/{station_id}`

Returns all primary equipment (generators, HVAC, water recycling, satellite dish) and their real-time health score.

#### Response (`HTTP 200`)
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "station_id": 1,
      "name": "Diesel Generator 1",
      "type": "generator",
      "status": "operational",
      "health_score": 96.5,
      "last_maintenance": "2026-08-15T00:00:00Z",
      "next_maintenance": "2026-11-15T00:00:00Z"
    }
  ]
}
```

---

### 2.4 Get Unified Digital Twin State
`GET /api/digital-twin/{station_id}`

Retrieves the complete current operational state of the station, synthesizing environment, energy, equipment, logistics, and active alerts.

#### Response (`HTTP 200`)
```json
{
  "success": true,
  "data": {
    "station_id": 1,
    "name": "Maitri Research Station",
    "code": "MAITRI",
    "status": "active",
    "environment": {
      "temperature": -24.5,
      "wind_speed": 18.2,
      "pressure": 984.1,
      "humidity": 68.0,
      "last_updated": "2026-09-29T12:00:00Z"
    },
    "energy": {
      "total_load_kw": 88.0,
      "solar_generation_kw": 20.0,
      "wind_generation_kw": 18.0,
      "dg_generation_kw": 50.0,
      "fuel_level_litres": 14200.0,
      "fuel_percentage": 71.0,
      "last_updated": "2026-09-29T12:00:00Z"
    },
    "equipment": {
      "status": "operational",
      "health_score": 96.5,
      "last_updated": "2026-09-29T12:00:00Z"
    },
    "logistics": {
      "fuel_days_remaining": 118.3,
      "resupply_urgency": "NORMAL",
      "last_updated": "2026-09-29T12:00:00Z"
    },
    "alerts": [],
    "last_updated": "2026-09-29T12:00:00Z",
    "data_source": "telemetry_service"
  }
}
```

---

### 2.5 Get Energy State
`GET /api/energy/{station_id}`

Retrieves energy microgrid metrics: solar kW, wind kW, diesel generator output, fuel tank percentage, and battery state-of-charge.

---

### 2.6 Get Logistics & Inventory State
`GET /api/logistics/{station_id}`

Returns current stock levels, fuel reserves, daily consumption rates, and days remaining before resupply window closure.
