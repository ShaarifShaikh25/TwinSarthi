import React, { useState } from 'react';
import { WHAT_IF_SCENARIOS, runLocalScenarioSimulation } from '../services/mockData';
import { apiService } from '../services/api';
import { SimulationResult, Recommendation } from '../types';
import { Badge } from '../components/ui/Badge';
import { DemoBadge } from '../components/ui/DemoBadge';
import { RecommendationModal } from '../components/ui/RecommendationModal';
import { Sliders, Play, RefreshCw, Sparkles, TrendingDown } from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export const WhatIfSimulator: React.FC = () => {
  const [selectedScenarioId, setSelectedScenarioId] = useState<string>('SCEN-01');
  const [scenarioParams, setScenarioParams] = useState<Record<string, any>>(
    WHAT_IF_SCENARIOS[0].defaultParams
  );
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [result, setResult] = useState<SimulationResult>(
    runLocalScenarioSimulation('SCEN-01', WHAT_IF_SCENARIOS[0].defaultParams)
  );
  const [selectedRec, setSelectedRec] = useState<Recommendation | null>(null);

  const handleScenarioChange = (id: string) => {
    setSelectedScenarioId(id);
    const scen = WHAT_IF_SCENARIOS.find((s) => s.id === id);
    if (scen) {
      setScenarioParams({ ...scen.defaultParams });
      // Instantly generate baseline scenario preview
      setResult(runLocalScenarioSimulation(id, scen.defaultParams));
    }
  };

  const handleRunSimulation = async () => {
    setIsRunning(true);
    try {
      // Try backend endpoint first
      const backendResult = await apiService.runScenarioSimulation(
        selectedScenarioId,
        scenarioParams
      );
      if (backendResult) {
        setResult(backendResult);
      } else {
        // Fallback to local scenario simulation generator with DEMO flag
        const localResult = runLocalScenarioSimulation(selectedScenarioId, scenarioParams);
        setResult(localResult);
      }
    } catch {
      const localResult = runLocalScenarioSimulation(selectedScenarioId, scenarioParams);
      setResult(localResult);
    } finally {
      setTimeout(() => setIsRunning(false), 800);
    }
  };

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-[#183153] font-mono tracking-tight flex items-center gap-2">
              <Sliders className="w-5 h-5 text-teal-600" />
              WHAT-IF SCENARIO SIMULATOR
            </h1>
            <Badge status="NORMAL" label="Predictive Engine Ready" />
          </div>
          <p className="text-xs text-slate-500 font-mono mt-1">
            Simulate polar weather shocks, generator failures, fuel surges & resupply delays
          </p>
        </div>

        {result.isDemo && (
          <DemoBadge
            label="DEMO SIMULATION"
            tooltip="Backend scenario simulation endpoint not available. Displaying mock predictive model output."
          />
        )}
      </div>

      {/* Main Grid: Scenario Controls & Simulation Results */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (1 col): Scenario Selector & Parameter Controls */}
        <div className="polar-card p-5 space-y-5 flex flex-col justify-between">
          <div className="space-y-4 font-mono text-xs">
            <div className="border-b border-slate-200 pb-2">
              <label className="text-[10px] text-teal-700 font-bold uppercase tracking-wider block mb-1">
                Select Test Scenario
              </label>
              <div className="space-y-1.5">
                {WHAT_IF_SCENARIOS.map((scen) => (
                  <button
                    key={scen.id}
                    onClick={() => handleScenarioChange(scen.id)}
                    className={`w-full text-left p-2.5 rounded border transition-colors ${
                      selectedScenarioId === scen.id
                        ? 'bg-teal-50 border-teal-600 text-teal-900 font-bold shadow-xs'
                        : 'bg-white border-slate-200 text-slate-700 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-teal-700 font-bold">{scen.id}</span>
                    </div>
                    <div className="text-xs font-semibold text-[#183153] mt-0.5">{scen.name}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Editable Scenario Parameters */}
            <div>
              <label className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block mb-2">
                Scenario Control Variables
              </label>
              <div className="bg-slate-50 p-3 rounded border border-slate-200 space-y-3">
                {Object.entries(scenarioParams).map(([key, val]) => (
                  <div key={key}>
                    <div className="flex justify-between text-[11px] text-slate-700 mb-1">
                      <span>{key}:</span>
                      <span className="text-teal-700 font-bold">{String(val)}</span>
                    </div>
                    {typeof val === 'number' ? (
                      <input
                        type="range"
                        min={0}
                        max={key.includes('Days') ? 30 : key.includes('Temp') ? 30 : 100}
                        value={val}
                        onChange={(e) =>
                          setScenarioParams({
                            ...scenarioParams,
                            [key]: parseFloat(e.target.value) || 0,
                          })
                        }
                        className="w-full accent-teal-600 bg-slate-200 cursor-pointer"
                      />
                    ) : (
                      <input
                        type="text"
                        value={String(val)}
                        onChange={(e) =>
                          setScenarioParams({
                            ...scenarioParams,
                            [key]: e.target.value,
                          })
                        }
                        className="w-full bg-white border border-slate-300 rounded px-2 py-1 text-[#183153] text-xs focus:outline-none focus:border-teal-600"
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Run Simulation Trigger Button */}
          <button
            onClick={handleRunSimulation}
            disabled={isRunning}
            className="w-full py-3 bg-teal-600 hover:bg-teal-700 text-white text-xs font-mono font-bold rounded shadow transition-all flex items-center justify-center gap-2"
          >
            {isRunning ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Computing Predictive Models...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white" />
                Execute What-If Simulation
              </>
            )}
          </button>
        </div>

        {/* Right Column (2 cols): Simulation Output & Impact Analysis */}
        <div className="lg:col-span-2 space-y-6">
          {/* Summary Banner */}
          <div className="polar-card p-4 border-l-4 border-l-teal-600">
            <div className="flex items-center justify-between font-mono text-xs mb-1">
              <span className="text-slate-500 uppercase tracking-wider font-semibold">Simulation Output Summary</span>
              <span className="text-teal-700 font-bold">{result.scenarioName}</span>
            </div>
            <p className="text-xs text-slate-800 font-mono bg-slate-50 p-3 rounded border border-slate-200">
              {result.summary}
            </p>
          </div>

          {/* KPI Delta Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
            <div className="polar-card p-3">
              <span className="text-[10px] text-slate-500 block uppercase font-semibold">Energy Surge</span>
              <span className="text-2xl font-bold text-amber-700">+{result.energyDeltaPct}%</span>
              <span className="text-[10px] text-slate-500 block mt-1">Load Demand Peak</span>
            </div>

            <div className="polar-card p-3">
              <span className="text-[10px] text-slate-500 block uppercase font-semibold">Fuel Days Buffer</span>
              <span className="text-2xl font-bold text-rose-600">{result.fuelDaysImpact} Days</span>
              <span className="text-[10px] text-slate-500 block mt-1">Reserve Reduction</span>
            </div>

            <div className="polar-card p-3">
              <span className="text-[10px] text-slate-500 block uppercase font-semibold">Stockout Risks</span>
              <span className="text-2xl font-bold text-amber-700">{result.inventoryRiskCount} Items</span>
              <span className="text-[10px] text-slate-500 block mt-1">Shortage Threshold</span>
            </div>

            <div className="polar-card p-3">
              <span className="text-[10px] text-slate-500 block uppercase font-semibold">Continuity Score</span>
              <span className="text-2xl font-bold text-emerald-700">{result.continuityScore}%</span>
              <span className="text-[10px] text-slate-500 block mt-1">Station Safety</span>
            </div>
          </div>

          {/* Forecast Line Chart */}
          <div className="polar-card p-4 space-y-3">
            <h3 className="text-xs font-bold font-mono text-[#183153] uppercase tracking-wider flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-teal-600" />
              72-Hour Simulated Station Trajectory
            </h3>

            <div className="h-60 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={result.metricsForecast} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="hoursAhead" tickFormatter={(h) => `+${h}h`} stroke="#64748B" fontSize={11} />
                  <YAxis stroke="#64748B" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '0.375rem', color: '#183153' }}
                  />
                  <Line type="monotone" dataKey="fuelLevel" name="Fuel Buffer (%)" stroke="#15803D" strokeWidth={2.5} />
                  <Line type="monotone" dataKey="energyDemand" name="Energy Demand (%)" stroke="#D97706" strokeWidth={2.5} />
                  <Line type="monotone" dataKey="continuity" name="Continuity (%)" stroke="#0D9488" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Recommended Mitigations (Human-in-the-Loop) */}
          <div className="polar-card p-4 space-y-3">
            <h3 className="text-xs font-bold font-mono text-[#183153] uppercase tracking-wider flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-teal-600" />
              AI Recommended Mitigation Actions ({result.recommendedActions.length})
            </h3>

            <div className="space-y-3 font-mono">
              {result.recommendedActions.map((rec) => (
                <div key={rec.id} className="bg-slate-50 p-3 rounded border border-slate-200 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-teal-800">{rec.title}</span>
                      <Badge status={rec.risk} label={`Risk: ${rec.risk}`} />
                    </div>
                    <p className="text-[11px] text-slate-600">{rec.description}</p>
                  </div>
                  <button
                    onClick={() => setSelectedRec(rec)}
                    className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded"
                  >
                    Evaluate Action
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Reusable Recommendation Review Modal */}
      {selectedRec && (
        <RecommendationModal
          recommendation={selectedRec}
          onClose={() => setSelectedRec(null)}
        />
      )}
    </div>
  );
};
