# POLAR-TWIN — Developer 3 Intelligence Integration Guide

This guide describes how **Developer 3 (AI / Risk / Simulation Lead)** integrates machine learning models, causal graphs, physics-informed neural networks (PINNs), and optimization engines into the POLAR-TWIN FastAPI backend.

---

## 1. Architectural Contract

```
Frontend / Real-Time Operations
           ↕ (REST / WebSockets)
FastAPI Backend Layer (Developer 2)
           ↓ (TwinContext)
BaseIntelligenceProvider (Contract)
           ↓
Developer 3 Intelligence Provider (Your ML Implementation)
           ↓ (Pydantic Result)
Backend Persistence & Real-Time Broadcast
```

The backend is fully decoupled from the machine learning implementation:
- **Zero Hardcoding**: Routes do not contain ML logic.
- **Fail-Safe Operation**: If no custom model is registered or if a model encounters an error, the backend automatically falls back to `FallbackIntelligenceProvider`, ensuring 100% operational uptime.
- **Automatic Persistence & Broadcasting**: The backend automatically persists your risk assessments, simulation runs, and resupply plans to the PostgreSQL/TimescaleDB database and streams real-time alerts & recommendations to connected station operators via `/ws/{station_id}`.

---

## 2. Pluggable Interface: `BaseIntelligenceProvider`

Located in [`app/services/intelligence/base.py`](file:///d:/sih%20bucket%20full%20ho%20giye%20dusra%20project/backend/app/services/intelligence/base.py).

Implement this interface to plug in your algorithms:

```python
from app.services.intelligence.base import BaseIntelligenceProvider
from app.schemas.intelligence import (
    TwinContext,
    EnergyPredictionRequest,
    EnergyPredictionResult,
    FuelPredictionRequest,
    FuelPredictionResult,
    AnomalyDetectionRequest,
    AnomalyDetectionResult,
    RiskCalculationRequest,
    RiskAssessmentResult,
    WhatIfSimulationRequest,
    WhatIfSimulationResult,
    ResupplyOptimizationRequest,
    ResupplyOptimizationResult,
)

class MyPolarTwinAI(BaseIntelligenceProvider):

    def predict_energy(self, context: TwinContext, request: EnergyPredictionRequest) -> EnergyPredictionResult:
        # Plug in your PyTorch / ONNX / XGBoost load forecast model
        ...

    def predict_fuel(self, context: TwinContext, request: FuelPredictionRequest) -> FuelPredictionResult:
        # Plug in your generator fuel burn & tank depletion model
        ...

    def detect_anomaly(self, context: TwinContext, request: AnomalyDetectionRequest) -> AnomalyDetectionResult:
        # Plug in IsolationForest / Autoencoder / Mahalanobis distance model
        ...

    def calculate_risk(self, context: TwinContext, request: RiskCalculationRequest) -> RiskAssessmentResult:
        # Plug in your Causal Bayesian Network / DAG for Cascading Risk (USP 1)
        ...

    def run_simulation(self, context: TwinContext, request: WhatIfSimulationRequest) -> WhatIfSimulationResult:
        # Plug in your Physics-Informed Digital Twin simulation (USP 2)
        ...

    def optimize_resupply(self, context: TwinContext, request: ResupplyOptimizationRequest) -> ResupplyOptimizationResult:
        # Plug in Mixed Integer Linear Programming (MILP) / Genetic Algorithm (USP 5)
        ...
```

---

## 3. How to Register Your Implementation

In your application startup (e.g., inside an extension module or service hook):

```python
from app.services.intelligence import register_intelligence_provider
from my_ml_package import MyPolarTwinAI

# Register your model provider:
register_intelligence_provider(MyPolarTwinAI())
```

Once registered, all incoming API requests and background jobs will seamlessly invoke your algorithms.

---

## 4. Input Provided to You: `TwinContext`

Before invoking your methods, the backend automatically queries the live digital twin, database records, and sensors to construct a `TwinContext` object:

| Field | Type | Description |
| :--- | :--- | :--- |
| `station_id` | `int` | Primary key identifier (1 = Maitri, 2 = Bharati) |
| `station_code` | `str` | `"MAITRI"` or `"BHARATI"` |
| `latitude`, `longitude` | `float` | Geo-coordinates on the Antarctic ice sheet |
| `digital_twin_state` | `dict` | Live unified twin state snapshot |
| `environment_state` | `dict` | Temperature (°C), wind speed (m/s), pressure, humidity |
| `energy_state` | `dict` | Generator status, battery state-of-charge, active electrical loads |
| `inventory_state` | `dict` | Fuel reserve %, rations, critical consumables |
| `equipment_state` | `list[dict]` | Equipment IDs, names, health scores, maintenance schedules |
| `recent_telemetry` | `list[dict]` | Historical sensor timeseries window |
| `active_alerts_count`| `int` | Number of currently active station safety alerts |

---

## 5. POLAR-TWIN Unique Selling Propositions (USPs)

The backend provides complete data contracts and persistence for all 5 core USPs:

1. **Cascading Risk Graph (USP 1)**:
   - Output `cascading_pathways: List[CascadingRiskNode]` in `calculate_risk`.
   - The backend tracks causal chains (e.g., `Generator 1 Trip` $\rightarrow$ `HVAC Freeze` $\rightarrow$ `Potable Water Line Failure` $\rightarrow$ `Evacuation Alert`).
   - Automatically generates a `PENDING` recommendation for the Station Controller if risk is `HIGH` or `CRITICAL`.

2. **What-If Simulation (USP 2)**:
   - Input `perturbations` dictionary (e.g. `{"temp_drop_c": -60.0, "primary_generator_fail": True}`).
   - Returns `survivability_score`, `metrics`, `critical_events`, and `contingencies`.
   - Persisted automatically to the `simulation_records` table.

3. **Mission Continuity & 4. Constraint-Aware Replanning (USPs 3 & 4)**:
   - Data contracts `MissionContinuityAssessment` and `ReplanningProposal` ready in `app.schemas.intelligence`.

4. **Resupply Optimization (USP 5)**:
   - Evaluates icebreaker sea approach windows and winter-over reserve margins.
   - Returns prioritized cargo list (`ResupplyItem`), total volume ($m^3$), and delay risk.
   - Persisted automatically to the `resupply_plans` table.

---

## 6. Endpoints Available in REST API

All routes mounted under `/api/intelligence`:
- `POST /api/intelligence/energy/predict`
- `POST /api/intelligence/fuel/predict`
- `POST /api/intelligence/anomalies/detect`
- `POST /api/intelligence/risk/calculate`
- `POST /api/intelligence/simulation/what-if` *(Requires CONTROLLER or ADMIN role)*
- `POST /api/intelligence/resupply/optimize` *(Requires CONTROLLER or ADMIN role)*
