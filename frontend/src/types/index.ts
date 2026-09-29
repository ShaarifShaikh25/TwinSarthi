export type StationId = 'maitri' | 'bharati';

export interface Station {
  id: StationId;
  name: string;
  location: string;
  coordinates: string;
  elevation: string;
  status: 'NORMAL' | 'WARNING' | 'CRITICAL' | 'OFFLINE';
  continuityScore: number;
  crewCount: number;
}

export interface Telemetry {
  timestamp: string;
  temperature: number; // °C
  energy: number; // % or kW
  fuel: number; // % or Liters
  priority: 'Normal' | 'High' | 'Critical' | string;
  alerts: string[];
  windSpeed?: number; // km/h
  humidity?: number; // %
  solarKw?: number;
  generatorKw?: number;
  batteryPct?: number;
  hvacPowerKw?: number;
  stationId?: StationId;
}

export interface Alert {
  id: string;
  timestamp: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  message: string;
  source: string;
  category: 'Environment' | 'Energy' | 'Infrastructure' | 'Logistics' | 'AI';
  resolved: boolean;
}

export interface Equipment {
  id: string;
  name: string;
  category: 'Generator' | 'HVAC' | 'Water' | 'Wastewater' | 'Communications' | 'Fuel Depot';
  status: 'NORMAL' | 'WARNING' | 'CRITICAL' | 'OFFLINE';
  health: number; // 0 - 100%
  lastMaintenance: string;
  nextMaintenance: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  location: string;
  specs: Record<string, string>;
  subsystemId: string;
}

export interface InventoryItem {
  id: string;
  name: string;
  category: 'Fuel' | 'Food' | 'Medicine' | 'Spare Parts' | 'Equipment';
  quantity: number;
  unit: string;
  consumptionRatePerDay: number;
  daysRemaining: number;
  predictedStockoutDate: string;
  resupplyStatus: 'Sufficient' | 'Pending Resupply' | 'Critical Shortage';
  minThreshold: number;
}

export interface RiskChainStep {
  stepNumber: number;
  title: string;
  description: string;
  severity: 'NORMAL' | 'WARNING' | 'CRITICAL';
  metric: string;
}

export interface Recommendation {
  id: string;
  title: string;
  category: 'Energy Optimization' | 'Emergency Protocol' | 'Logistics Resupply' | 'Maintenance';
  description: string;
  impact: string;
  risk: 'LOW' | 'MEDIUM' | 'HIGH';
  suggestedAction: string;
  parameters?: Record<string, any>;
  status: 'PENDING' | 'APPROVED' | 'MODIFIED' | 'REJECTED';
  modifiedParameters?: Record<string, any>;
  timestamp: string;
}

export interface WhatIfScenario {
  id: string;
  name: string;
  description: string;
  defaultParams: Record<string, number | string | boolean>;
}

export interface SimulationResult {
  scenarioId: string;
  scenarioName: string;
  timestamp: string;
  isDemo: boolean;
  summary: string;
  energyDeltaPct: number;
  fuelDaysImpact: number;
  inventoryRiskCount: number;
  continuityScore: number;
  recommendedActions: Recommendation[];
  metricsForecast: {
    hoursAhead: number;
    fuelLevel: number;
    energyDemand: number;
    temperature: number;
    continuity: number;
  }[];
}

export interface ConnectionState {
  isConnected: boolean;
  mode: 'LIVE' | 'DEMO';
  lastPayloadTime: string | null;
  error?: string | null;
}
