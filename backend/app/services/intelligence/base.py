"""app/services/intelligence/base.py

Abstract Base Provider Contract for POLAR-TWIN Intelligence (Phase 9).
Developer 3 implements this interface to connect ML algorithms, causal inference graphs,
thermodynamic models, and logistics optimizers to the FastAPI backend.
"""

from abc import ABC, abstractmethod

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


class BaseIntelligenceProvider(ABC):
    """Abstract interface defining the contract between FastAPI Backend (Developer 2)
    and AI / Risk / Simulation Intelligence Modules (Developer 3).
    """

    @abstractmethod
    def predict_energy(
        self,
        context: TwinContext,
        request: EnergyPredictionRequest,
    ) -> EnergyPredictionResult:
        """Predict station electrical and thermal power demand over horizon."""
        pass

    @abstractmethod
    def predict_fuel(
        self,
        context: TwinContext,
        request: FuelPredictionRequest,
    ) -> FuelPredictionResult:
        """Forecast diesel fuel consumption and calculate remaining days of autonomy."""
        pass

    @abstractmethod
    def detect_anomaly(
        self,
        context: TwinContext,
        request: AnomalyDetectionRequest,
    ) -> AnomalyDetectionResult:
        """Analyze sensor telemetry streams to detect multivariate anomalies."""
        pass

    @abstractmethod
    def calculate_risk(
        self,
        context: TwinContext,
        request: RiskCalculationRequest,
    ) -> RiskAssessmentResult:
        """Compute operational risk score and trace cascading failure paths (USP 1)."""
        pass

    @abstractmethod
    def run_simulation(
        self,
        context: TwinContext,
        request: WhatIfSimulationRequest,
    ) -> WhatIfSimulationResult:
        """Run what-if scenario simulations under polar environmental stress (USP 2)."""
        pass

    @abstractmethod
    def optimize_resupply(
        self,
        context: TwinContext,
        request: ResupplyOptimizationRequest,
    ) -> ResupplyOptimizationResult:
        """Compute optimal icebreaker resupply window and cargo priority matrix (USP 5)."""
        pass
