import {
  Station,
  Telemetry,
  Equipment,
  InventoryItem,
  RiskChainStep,
  Recommendation,
  WhatIfScenario,
  SimulationResult,
} from '../types';

export const STATIONS: Station[] = [
  {
    id: 'maitri',
    name: 'Maitri Research Station',
    location: 'Schirmacher Oasis, Queen Maud Land',
    coordinates: '70.7667° S, 11.7333° E',
    elevation: '117 m',
    status: 'NORMAL',
    continuityScore: 94.8,
    crewCount: 24,
  },
  {
    id: 'bharati',
    name: 'Bharati Research Station',
    location: 'Larsemann Hills, Prydz Bay',
    coordinates: '69.4075° S, 76.1914° E',
    elevation: '35 m',
    status: 'WARNING',
    continuityScore: 88.5,
    crewCount: 18,
  },
];

export const INITIAL_TELEMETRY: Record<string, Telemetry> = {
  maitri: {
    timestamp: new Date().toISOString(),
    temperature: -28.4,
    energy: 92.5,
    fuel: 86.0,
    priority: 'Normal',
    alerts: [],
    windSpeed: 42.0,
    humidity: 65,
    solarKw: 38.5,
    generatorKw: 105.0,
    batteryPct: 91.0,
    hvacPowerKw: 42.0,
  },
  bharati: {
    timestamp: new Date().toISOString(),
    temperature: -34.8,
    energy: 78.2,
    fuel: 68.4,
    priority: 'High',
    alerts: ['High HVAC Thermal Demand', 'Generator G2 Vibration Anomaly'],
    windSpeed: 68.5,
    humidity: 78,
    solarKw: 15.0,
    generatorKw: 145.0,
    batteryPct: 76.5,
    hvacPowerKw: 58.5,
  },
};

export const INITIAL_EQUIPMENT: Equipment[] = [
  {
    id: 'GEN-01',
    name: 'Main Diesel Generator G1 (Cummins 250kVA)',
    category: 'Generator',
    status: 'NORMAL',
    health: 96,
    lastMaintenance: '2026-08-15',
    nextMaintenance: '2026-10-15',
    riskLevel: 'LOW',
    location: 'Power House Module A',
    subsystemId: 'sub-energy-01',
    specs: { FuelType: 'Polar Diesel', Output: '250 kVA', Voltage: '400V 3Ph' },
  },
  {
    id: 'GEN-02',
    name: 'Auxiliary Diesel Generator G2 (Cummins 250kVA)',
    category: 'Generator',
    status: 'WARNING',
    health: 74,
    lastMaintenance: '2026-07-10',
    nextMaintenance: '2026-09-30',
    riskLevel: 'MEDIUM',
    location: 'Power House Module A',
    subsystemId: 'sub-energy-02',
    specs: { FaultCode: 'E-402 High Vibration', Temp: '88°C' },
  },
  {
    id: 'HVAC-01',
    name: 'Living Quarters Thermal Loop A',
    category: 'HVAC',
    status: 'NORMAL',
    health: 92,
    lastMaintenance: '2026-08-01',
    nextMaintenance: '2026-11-01',
    riskLevel: 'LOW',
    location: 'Main Habitation Module',
    subsystemId: 'sub-hvac-01',
    specs: { Airflow: '4500 CFM', GlycolPressure: '3.2 Bar' },
  },
  {
    id: 'HVAC-02',
    name: 'Laboratory Wing Dual Heat Pump',
    category: 'HVAC',
    status: 'CRITICAL',
    health: 48,
    lastMaintenance: '2026-05-12',
    nextMaintenance: '2026-09-20 (Overdue)',
    riskLevel: 'HIGH',
    location: 'Science Lab Module B',
    subsystemId: 'sub-hvac-02',
    specs: { DefrostError: 'E-701 Defrost Heater Relay Failed', DuctTemp: '-2°C' },
  },
  {
    id: 'WTR-01',
    name: 'Sub-Glacial Meltwater Extraction Pump',
    category: 'Water',
    status: 'NORMAL',
    health: 89,
    lastMaintenance: '2026-08-20',
    nextMaintenance: '2026-10-20',
    riskLevel: 'LOW',
    location: 'Priydarshini Lake Intake',
    subsystemId: 'sub-water-01',
    specs: { FlowRate: '1200 L/h', TraceHeating: 'Active (4.5kW)' },
  },
  {
    id: 'WST-01',
    name: 'Graywater Bioreactor & Evaporator Unit',
    category: 'Wastewater',
    status: 'NORMAL',
    health: 94,
    lastMaintenance: '2026-08-28',
    nextMaintenance: '2026-11-28',
    riskLevel: 'LOW',
    location: 'Utilities Block C',
    subsystemId: 'sub-wst-01',
    specs: { Efficiency: '98%', SludgeLevel: '14%' },
  },
  {
    id: 'COM-01',
    name: 'C-Band Satellite Ground Station Antenna',
    category: 'Communications',
    status: 'NORMAL',
    health: 98,
    lastMaintenance: '2026-09-01',
    nextMaintenance: '2026-12-01',
    riskLevel: 'LOW',
    location: 'Radome Dome North',
    subsystemId: 'sub-com-01',
    specs: { Bandwidth: '25 Mbps Up / 50 Mbps Down', RadomeHeater: 'AUTO' },
  },
  {
    id: 'FUEL-01',
    name: 'Primary Fuel Storage Matrix (Tanks 1-4)',
    category: 'Fuel Depot',
    status: 'NORMAL',
    health: 91,
    lastMaintenance: '2026-07-15',
    nextMaintenance: '2026-11-15',
    riskLevel: 'LOW',
    location: 'Exterior Tank Farm',
    subsystemId: 'sub-fuel-01',
    specs: { Capacity: '250,000 L', Level: '215,000 L', Temp: '-15°C' },
  },
];

export const INITIAL_INVENTORY: InventoryItem[] = [
  {
    id: 'INV-FUEL-01',
    name: 'Arctic Aviation & Generator Fuel (Jet A-1 / Polar Diesel)',
    category: 'Fuel',
    quantity: 215000,
    unit: 'Liters',
    consumptionRatePerDay: 1850,
    daysRemaining: 116,
    predictedStockoutDate: '2027-01-23',
    resupplyStatus: 'Sufficient',
    minThreshold: 30000,
  },
  {
    id: 'INV-FOOD-01',
    name: 'Freeze-Dried Rations & Cold-Storage Provisions',
    category: 'Food',
    quantity: 4200,
    unit: 'Man-Days',
    consumptionRatePerDay: 42,
    daysRemaining: 100,
    predictedStockoutDate: '2027-01-07',
    resupplyStatus: 'Sufficient',
    minThreshold: 1000,
  },
  {
    id: 'INV-MED-01',
    name: 'Critical Polar Medical & Trauma Surgical Supplies',
    category: 'Medicine',
    quantity: 18,
    unit: 'Full Kits',
    consumptionRatePerDay: 0.05,
    daysRemaining: 360,
    predictedStockoutDate: '2027-09-24',
    resupplyStatus: 'Sufficient',
    minThreshold: 5,
  },
  {
    id: 'INV-SPARE-01',
    name: 'Cummins Generator Replacement Fuel Filters & Injection Nozzles',
    category: 'Spare Parts',
    quantity: 4,
    unit: 'Sets',
    consumptionRatePerDay: 0.08,
    daysRemaining: 50,
    predictedStockoutDate: '2026-11-18',
    resupplyStatus: 'Pending Resupply',
    minThreshold: 3,
  },
  {
    id: 'INV-SPARE-02',
    name: 'Glycol Heat Exchanger Seals & Circulator Valves',
    category: 'Spare Parts',
    quantity: 2,
    unit: 'Kits',
    consumptionRatePerDay: 0.05,
    daysRemaining: 40,
    predictedStockoutDate: '2026-11-08',
    resupplyStatus: 'Critical Shortage',
    minThreshold: 4,
  },
];

export const CAUSAL_RISK_CHAIN: RiskChainStep[] = [
  {
    stepNumber: 1,
    title: 'Severe Polar Blizzard (-42°C, 85 km/h Wind)',
    description: 'Extreme ambient temperature drop increases station thermal dissipation exponentially.',
    severity: 'WARNING',
    metric: 'Ambient Temp: -42.5°C',
  },
  {
    stepNumber: 2,
    title: 'HVAC Thermal Loop Demand Surge',
    description: 'Habitation & Lab heating systems automatically ramp up to 100% duty cycle.',
    severity: 'WARNING',
    metric: 'Thermal Demand +45%',
  },
  {
    stepNumber: 3,
    title: 'Microgrid Electrical Load Peak',
    description: 'Electric glycol trace heating & booster pumps engage simultaneously.',
    severity: 'WARNING',
    metric: 'Microgrid Load: 185 kW',
  },
  {
    stepNumber: 4,
    title: 'Generator G1 + G2 Dual Parallel Dispatch',
    description: 'Secondary generator G2 auto-starts to handle peak kW load.',
    severity: 'WARNING',
    metric: 'Generator Fuel Burn: 92 L/h',
  },
  {
    stepNumber: 5,
    title: 'Fuel Reserve Depletion Rate Acceleration',
    description: 'Daily fuel consumption increases from 1,850 L/day to 2,550 L/day.',
    severity: 'CRITICAL',
    metric: 'Days Remaining: Reduced by 28 Days',
  },
  {
    stepNumber: 6,
    title: 'Vessel Resupply Window Vulnerability',
    description: 'If resupply vessel MV Vasiliy Golovnin is delayed by >7 days, reserve falls below emergency minimum.',
    severity: 'CRITICAL',
    metric: 'Mission Continuity Risk: HIGH',
  },
];

export const INITIAL_RECOMMENDATIONS: Recommendation[] = [
  {
    id: 'REC-2026-001',
    title: 'Optimum Thermal Zone Partitioning',
    category: 'Energy Optimization',
    description: 'Reduce ambient temperature in unoccupied Science Lab B from 21°C to 12°C during severe blizzard hours.',
    impact: 'Reduces HVAC electrical demand by 18 kW, saving ~220 Liters of polar diesel per day.',
    risk: 'LOW',
    suggestedAction: 'Lower thermostat setpoint for Zone B & lock circulation dampers.',
    parameters: { targetZone: 'Lab Module B', setpointTempC: 12, DurationHours: 48 },
    status: 'PENDING',
    timestamp: new Date().toISOString(),
  },
  {
    id: 'REC-2026-002',
    title: 'Generator G2 Vibration Mitigation & Load Balancing',
    category: 'Maintenance',
    description: 'G2 generator shows 8.4mm/s RMS vibration anomaly. Throttle G2 to 40% load and shift remaining base load to Microgrid Battery Storage.',
    impact: 'Prevents catastrophic bearing failure on G2 until scheduled maintenance window.',
    risk: 'MEDIUM',
    suggestedAction: 'Engage Battery Energy Storage System (BESS) peak-shaving algorithm.',
    parameters: { maxG2LoadKw: 60, bessDischargeRateKw: 45 },
    status: 'PENDING',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
  },
];

export const WHAT_IF_SCENARIOS: WhatIfScenario[] = [
  {
    id: 'SCEN-01',
    name: 'Resupply Vessel MV Vasiliy Golovnin Delayed by 7 Days',
    description: 'Simulates icepack blockage causing a 7-day delay in seasonal fuel & provisions unlading.',
    defaultParams: { delayDays: 7, severeWeatherFactor: 1.0, generatorFailureCount: 0 },
  },
  {
    id: 'SCEN-02',
    name: 'Catastrophic Failure of Main Generator G1',
    description: 'Simulates complete electrical lockout of G1 unit forcing single-generator operation on G2.',
    defaultParams: { g1Status: 'FAILED', g2LoadSharePct: 100, batteryCapacityBufferHours: 12 },
  },
  {
    id: 'SCEN-03',
    name: 'Severe Ambient Temperature Drop (-10°C Delta)',
    description: 'Simulates extreme polar vortex pushing temperatures down to -48°C for 5 consecutive days.',
    defaultParams: { tempDropC: -10, windSpeedKm: 95, durationHours: 120 },
  },
  {
    id: 'SCEN-04',
    name: 'Fuel Consumption Surge (+20% Burn Rate)',
    description: 'Simulates fuel leakage or high thermal loss across external piping lines.',
    defaultParams: { fuelSurgePct: 20, traceHeatingOverdrive: true },
  },
  {
    id: 'SCEN-05',
    name: '72-Hour Continuous Polar Blizzard Emergency',
    description: 'Simulates complete blackout of solar generation array with max heating & communications active.',
    defaultParams: { blizzardHours: 72, solarYieldPct: 0, windTurbineLockout: true },
  },
];

export function runLocalScenarioSimulation(scenarioId: string, customParams: Record<string, any>): SimulationResult {
  const scenario = WHAT_IF_SCENARIOS.find((s) => s.id === scenarioId) || WHAT_IF_SCENARIOS[0];
  
  let fuelDaysImpact = -7;
  let energyDeltaPct = 14.5;
  let inventoryRiskCount = 2;
  let continuityScore = 82.4;
  let summary = `Simulation complete for [${scenario.name}]. Predicted fuel reserve impact: -7 Days. Energy load surge: +14.5%.`;

  if (scenarioId === 'SCEN-01') {
    fuelDaysImpact = -7;
    energyDeltaPct = 4.2;
    inventoryRiskCount = 3;
    continuityScore = 78.5;
    summary = 'Vessel delay reduces safety fuel buffer below NCPOR threshold (minimum 30 days buffer required).';
  } else if (scenarioId === 'SCEN-02') {
    fuelDaysImpact = -12;
    energyDeltaPct = 28.0;
    inventoryRiskCount = 4;
    continuityScore = 65.0;
    summary = 'G1 Failure triggers emergency load shedding protocol. Battery storage depletes in 14.2 hours if unassisted.';
  } else if (scenarioId === 'SCEN-03') {
    fuelDaysImpact = -9;
    energyDeltaPct = 22.4;
    inventoryRiskCount = 2;
    continuityScore = 84.0;
    summary = '-10°C Ambient drop accelerates daily diesel burn rate by +480 L/day across thermal loops.';
  } else if (scenarioId === 'SCEN-04') {
    fuelDaysImpact = -18;
    energyDeltaPct = 20.0;
    inventoryRiskCount = 3;
    continuityScore = 74.2;
    summary = '20% Fuel burn surge accelerates stockout date from Jan 23 to Jan 05.';
  } else if (scenarioId === 'SCEN-05') {
    fuelDaysImpact = -10;
    energyDeltaPct = 35.0;
    inventoryRiskCount = 4;
    continuityScore = 71.8;
    summary = '72-Hour Blizzard eliminates solar contribution and forces G1+G2 continuous dual load operation.';
  }

  return {
    scenarioId,
    scenarioName: scenario.name,
    timestamp: new Date().toISOString(),
    isDemo: true, // Clearly labeled as DEMO simulation
    summary,
    energyDeltaPct,
    fuelDaysImpact,
    inventoryRiskCount,
    continuityScore,
    recommendedActions: [
      {
        id: `SIM-REC-${Date.now()}-1`,
        title: 'Execute Station Peak-Load Shedding Protocol',
        category: 'Energy Optimization',
        description: 'Disable non-essential sauna heaters, exterior floodlights, and secondary core drills.',
        impact: 'Saves 35 kW load, offsetting +18.5% of predicted surge.',
        risk: 'LOW',
        suggestedAction: 'Shed Load Group 3 (Non-Critical Utilities)',
        parameters: { shedKw: 35, affectedModules: ['Sauna', 'Outpost Drill B'] },
        status: 'PENDING',
        timestamp: new Date().toISOString(),
      },
      {
        id: `SIM-REC-${Date.now()}-2`,
        title: 'Re-route Glycol Loop to High-Efficiency Auxiliary Boiler',
        category: 'Emergency Protocol',
        description: 'Engage secondary waste-heat recovery loop from G2 exhaust to supplement main HVAC.',
        impact: 'Reduces direct diesel heater consumption by 180 L/day.',
        risk: 'MEDIUM',
        suggestedAction: 'Open Bypass Valve V-104 & start Heat Exchanger HX-02',
        parameters: { bypassValve: 'V-104', targetExchanger: 'HX-02' },
        status: 'PENDING',
        timestamp: new Date().toISOString(),
      },
    ],
    metricsForecast: [
      { hoursAhead: 0, fuelLevel: 86, energyDemand: 100, temperature: -28, continuity: 94 },
      { hoursAhead: 12, fuelLevel: 82, energyDemand: 118, temperature: -34, continuity: 91 },
      { hoursAhead: 24, fuelLevel: 77, energyDemand: 125, temperature: -38, continuity: 86 },
      { hoursAhead: 36, fuelLevel: 71, energyDemand: 128, temperature: -40, continuity: 82 },
      { hoursAhead: 48, fuelLevel: 65, energyDemand: 122, temperature: -36, continuity: 80 },
      { hoursAhead: 72, fuelLevel: 54, energyDemand: 115, temperature: -31, continuity: 84 },
    ],
  };
}
