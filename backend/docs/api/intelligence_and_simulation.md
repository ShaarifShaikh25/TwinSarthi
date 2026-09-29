# AI, Risk & Simulation Integration Interfaces (Developer 3 API)

## 1. Modular Interface Architecture
Developer 3 owns the implementation of AI models, Physics Simulations, and Optimization algorithms. The backend provides clean, loosely-coupled service interfaces and REST endpoints so ML models can be plugged in without refactoring FastAPI routes.

```
API Route (/api/intelligence/...)
              ↓
  Service Interface (IntelligenceService)
              ↓
   Developer 3 Intelligence Provider
  (implements BaseIntelligenceProvider)
              ↓
  Backend Result Processing
              ↓
 Database / Cache Persistence
              ↓
 WebSocket Event Broadcast (/ws/{station_id})
              ↓
   Frontend Visualization
```

---

## 2. Core Service Methods & Endpoints

### 2.1 Energy Prediction
`POST /api/intelligence/predict-energy`

Forecasts multi-hour electrical demand, renewable generation (solar PV & wind), and storage state-of-charge.

#### Request Body
```json
{
  "station_code": "MAITRI",
  "horizon_hours": 24,
  "ambient_temperature": -25.0,
  "wind_speed_forecast": 15.0
}
```

---

### 2.2 Fuel Depletion Prediction
`POST /api/intelligence/predict-fuel`

Projects generator diesel consumption, burn rate, and days of autonomous survival under specified heating and weather scenarios.

#### Request Body
```json
{
  "station_code": "BHARATI",
  "current_stock_litres": 12000.0,
  "burn_rate_litres_per_hour": 35.0,
  "target_days": 180
}
```

---

### 2.3 Sensor Anomaly Detection
`POST /api/intelligence/detect-anomaly`

Identifies multivariate sensor drift, freezing anomalies, stuck sensors, and physical inconsistencies.

#### Request Body
```json
{
  "station_code": "MAITRI",
  "sensor_id": 1,
  "sensor_type": "temperature",
  "recent_values": [-22.0, -22.1, -22.0, -999.0],
  "expected_range_min": -60.0,
  "expected_range_max": 10.0
}
```

---

### 2.4 Cascading Risk Assessment
`POST /api/intelligence/calculate-risk`

Evaluates interdependent causal failure propagation across Antarctic life-support subsystems (e.g. Blizzard → Solar Failure → DG Overload → Freeze Risk).

#### Request Body
```json
{
  "station_code": "MAITRI",
  "wind_speed": 42.0,
  "temperature": -45.0,
  "primary_dg_status": "degraded",
  "fuel_percentage": 25.0
}
```

---

### 2.5 What-If Operational Simulation
`POST /api/simulation/run` or `POST /api/intelligence/run-simulation`

Simulates hypothetical disaster and operational scenarios:
- `DG_FAILURE`: Primary diesel generator trip under extreme blizzard.
- `BLIZZARD_SEVEN_DAYS`: Sustained zero solar generation and maximum heating load.
- `FUEL_LEAK`: Accelerated storage tank loss.

---

### 2.6 Resupply Logistics Optimization
`POST /api/intelligence/optimize-resupply`

Generates cargo prioritization matrices and weather-window resupply recommendations based on ship icebreaker transit windows.
