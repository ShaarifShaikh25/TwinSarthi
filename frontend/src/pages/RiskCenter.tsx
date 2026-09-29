import React, { useState } from 'react';
import { useStation } from '../hooks/useStation';
import { CAUSAL_RISK_CHAIN } from '../services/mockData';
import { Badge } from '../components/ui/Badge';
import { ShieldAlert, AlertTriangle, Layers } from 'lucide-react';

export const RiskCenter: React.FC = () => {
  const { currentStation, telemetry } = useStation();

  const [alerts, setAlerts] = useState([
    {
      id: 'ALT-101',
      timestamp: '2026-09-29T16:30:00Z',
      severity: 'WARNING',
      message: 'Generator G2 high vibration level detected (8.4 mm/s RMS)',
      category: 'Infrastructure',
      resolved: false,
    },
    {
      id: 'ALT-102',
      timestamp: '2026-09-29T15:10:00Z',
      severity: 'CRITICAL',
      message: 'Science Lab B Defrost Heater Relay Failed - Temperature drop to -2°C',
      category: 'Infrastructure',
      resolved: false,
    },
    {
      id: 'ALT-103',
      timestamp: '2026-09-29T12:00:00Z',
      severity: 'INFO',
      message: 'Polar Blizzard warning issued by NCPOR Meteorological Center',
      category: 'Environment',
      resolved: true,
    },
  ]);

  const toggleResolve = (id: string) => {
    setAlerts((prev) =>
      prev.map((a) => (a.id === id ? { ...a, resolved: !a.resolved } : a))
    );
  };

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-[#183153] font-mono tracking-tight flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-rose-600" />
              RISK CENTER & CAUSAL ANOMALY MATRIX
            </h1>
            <Badge status="WARNING" label="Risk Index: 28/100 (Medium)" />
          </div>
          <p className="text-xs text-slate-500 font-mono mt-1">
            Station risk scoring, active alerts, anomaly timelines & multi-stage causal chain analysis
          </p>
        </div>
      </div>

      {/* Category Risk Matrix Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 font-mono text-xs">
        <div className="polar-card p-3 border-l-4 border-l-emerald-600">
          <span className="text-slate-500 text-[10px] uppercase block font-semibold">Environment</span>
          <span className="text-lg font-bold text-emerald-700">LOW (12%)</span>
          <p className="text-[10px] text-slate-500 mt-1">Wind 42 km/h</p>
        </div>

        <div className="polar-card p-3 border-l-4 border-l-emerald-600">
          <span className="text-slate-500 text-[10px] uppercase block font-semibold">Energy Microgrid</span>
          <span className="text-lg font-bold text-emerald-700">LOW (18%)</span>
          <p className="text-[10px] text-slate-500 mt-1">Fuel 86% Buffer</p>
        </div>

        <div className="polar-card p-3 border-l-4 border-l-amber-500">
          <span className="text-slate-500 text-[10px] uppercase block font-semibold">Infrastructure</span>
          <span className="text-lg font-bold text-amber-700">MEDIUM (42%)</span>
          <p className="text-[10px] text-slate-500 mt-1">G2 & Lab B Anomalies</p>
        </div>

        <div className="polar-card p-3 border-l-4 border-l-emerald-600">
          <span className="text-slate-500 text-[10px] uppercase block font-semibold">Logistics Supply</span>
          <span className="text-lg font-bold text-emerald-700">LOW (20%)</span>
          <p className="text-[10px] text-slate-500 mt-1">Vessel 42d ETA</p>
        </div>

        <div className="polar-card p-3 border-l-4 border-l-emerald-600">
          <span className="text-slate-500 text-[10px] uppercase block font-semibold">Mission Continuity</span>
          <span className="text-lg font-bold text-emerald-700">NOMINAL (94.8%)</span>
          <p className="text-[10px] text-slate-500 mt-1">Zero Lockout</p>
        </div>
      </div>

      {/* Visual Cascading RiskChain Component */}
      <div className="polar-card p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between border-b border-slate-200 pb-3 gap-2">
          <div>
            <h2 className="text-sm font-bold font-mono text-[#183153] uppercase tracking-wider flex items-center gap-2">
              <Layers className="w-4 h-4 text-teal-600" />
              Cascading Causal Risk Chain Model
            </h2>
            <p className="text-xs text-slate-500 font-mono">
              Visual propagation sequence mapping ambient polar triggers to station mission impact
            </p>
          </div>

          <span className="text-[10px] px-2.5 py-1 bg-slate-100 text-teal-800 border border-slate-200 rounded font-mono font-bold">
            ★ Illustrative Causal Pathway (NCPOR Engine Model)
          </span>
        </div>

        {/* Risk Chain Steps horizontal sequence */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3">
          {CAUSAL_RISK_CHAIN.map((step) => (
            <div
              key={step.stepNumber}
              className={`p-3 rounded border font-mono text-xs flex flex-col justify-between space-y-2 relative ${
                step.severity === 'CRITICAL'
                  ? 'bg-rose-50 border-rose-200 text-rose-900'
                  : 'bg-white border-slate-200 text-slate-800'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1 text-[10px]">
                  <span className="text-teal-700 font-bold">STAGE 0{step.stepNumber}</span>
                  <Badge status={step.severity} />
                </div>
                <h4 className="text-xs font-bold leading-tight mb-1 text-[#183153]">{step.title}</h4>
                <p className="text-[10px] text-slate-600 leading-normal">{step.description}</p>
              </div>

              <div className="pt-2 border-t border-slate-200 text-[10px] font-bold text-amber-700">
                {step.metric}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Active Station Anomaly Log */}
      <div className="polar-card p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-200 pb-3 font-mono">
          <h3 className="text-sm font-bold text-[#183153] uppercase tracking-wider flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            Station Alert & Anomaly History Log
          </h3>
          <span className="text-xs text-slate-500">Total Logged: {alerts.length} Events</span>
        </div>

        <div className="space-y-3 font-mono text-xs">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className={`p-3 rounded border flex flex-wrap items-center justify-between gap-3 ${
                alert.resolved
                  ? 'bg-slate-50 border-slate-200 opacity-60'
                  : alert.severity === 'CRITICAL'
                  ? 'bg-rose-50/50 border-rose-200'
                  : 'bg-white border-slate-200'
              }`}
            >
              <div className="flex items-center gap-3">
                <Badge status={alert.severity} />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-teal-800 font-bold">{alert.id}</span>
                    <span className="text-[10px] text-slate-500">{alert.timestamp}</span>
                    <span className="text-[10px] text-teal-700 font-semibold">[{alert.category}]</span>
                  </div>
                  <p className="text-xs text-slate-800 mt-0.5 font-medium">{alert.message}</p>
                </div>
              </div>

              <button
                onClick={() => toggleResolve(alert.id)}
                className={`px-3 py-1 text-xs rounded transition-colors ${
                  alert.resolved
                    ? 'bg-slate-100 text-slate-500'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 font-semibold'
                }`}
              >
                {alert.resolved ? 'Mark Unresolved' : 'Resolve Alert'}
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
