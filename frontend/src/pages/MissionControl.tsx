import React, { useState } from 'react';
import { useStation } from '../hooks/useStation';
import { Badge } from '../components/ui/Badge';
import { DemoBadge } from '../components/ui/DemoBadge';
import { RecommendationModal } from '../components/ui/RecommendationModal';
import { Recommendation } from '../types';
import { formatTemp, formatDateTime, getContinuityScoreColor } from '../utils/formatters';
import {
  Thermometer,
  Wind,
  Zap,
  ShieldAlert,
  Activity,
  ArrowUpRight,
  CheckCircle2,
  Cpu,
  Truck,
  Sparkles,
} from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const mockTelemetryHistory = [
  { time: '12:00', temp: -27.2, energy: 94.0, fuel: 88.5, load: 110 },
  { time: '13:00', temp: -28.0, energy: 93.2, fuel: 88.0, load: 112 },
  { time: '14:00', temp: -29.5, energy: 91.8, fuel: 87.4, load: 118 },
  { time: '15:00', temp: -31.2, energy: 89.0, fuel: 86.8, load: 125 },
  { time: '16:00', temp: -33.0, energy: 86.5, fuel: 86.2, load: 138 },
  { time: '17:00', temp: -28.4, energy: 92.5, fuel: 86.0, load: 108 },
];

export const MissionControl: React.FC = () => {
  const {
    currentStation,
    telemetry,
    equipment,
    inventory,
    recommendations,
    connectionState,
  } = useStation();

  const [selectedRec, setSelectedRec] = useState<Recommendation | null>(null);

  const criticalEquipmentCount = equipment.filter(
    (e) => e.status === 'CRITICAL' || e.status === 'WARNING'
  ).length;

  const lowInventoryCount = inventory.filter(
    (i) => i.resupplyStatus !== 'Sufficient'
  ).length;

  const estimatedFuelDays = Math.round(
    (inventory.find((i) => i.category === 'Fuel')?.quantity || 215000) / 1850
  );

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Page Title & Status Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-[#183153] font-mono tracking-tight">
              MISSION CONTROL — {currentStation.name.toUpperCase()}
            </h1>
            <Badge status={currentStation.status} size="md" />
          </div>
          <p className="text-xs text-slate-500 font-mono mt-1">
            Real-time telemetry, predictive analytics & station continuity engine
          </p>
        </div>

        <div className="flex items-center gap-3">
          {connectionState.mode === 'DEMO' && (
            <DemoBadge label="OFFLINE DEMO" tooltip="Streaming simulated station telemetry." />
          )}
          <div className="text-xs font-mono text-slate-600 bg-white px-3 py-1.5 rounded border border-slate-200 shadow-xs">
            Last Update: {formatDateTime(telemetry.timestamp)}
          </div>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Mission Continuity Score */}
        <div className="polar-card p-4 relative overflow-hidden">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider font-semibold">Mission Continuity</span>
            <Activity className="w-4 h-4 text-teal-600" />
          </div>
          <div className="flex items-baseline gap-2">
            <span className={`text-3xl font-extrabold font-mono ${getContinuityScoreColor(currentStation.continuityScore)}`}>
              {currentStation.continuityScore}%
            </span>
            <span className="text-xs text-emerald-700 flex items-center font-mono font-semibold">
              <ArrowUpRight className="w-3.5 h-3.5" /> Nominal
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono">
            Zero station-critical failure alerts active
          </p>
        </div>

        {/* Ambient Temperature & Wind */}
        <div className="polar-card p-4">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider font-semibold">Station Weather</span>
            <Thermometer className="w-4 h-4 text-sky-600" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold font-mono text-[#183153]">
              {formatTemp(telemetry.temperature)}
            </span>
            <div className="text-right">
              <div className="flex items-center gap-1 text-xs text-slate-700 font-mono font-semibold">
                <Wind className="w-3.5 h-3.5 text-teal-600" />
                {telemetry.windSpeed || 42} km/h
              </div>
              <span className="text-[10px] text-slate-500 font-mono">Wind Chill: -41°C</span>
            </div>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono">
            Polar Vortex: Moderate Intensity
          </p>
        </div>

        {/* Fuel Reserve & Estimated Days */}
        <div className="polar-card p-4">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider font-semibold">Fuel Reserve Buffer</span>
            <Zap className="w-4 h-4 text-amber-600" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold font-mono text-emerald-700">
              {telemetry.fuel}%
            </span>
            <span className="text-xs font-mono px-2 py-0.5 bg-emerald-50 text-emerald-800 rounded border border-emerald-200 font-semibold">
              ~{estimatedFuelDays} Days Operational
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2 font-mono">
            Burn Rate: ~1,850 Liters/Day
          </p>
        </div>

        {/* System Warnings & Inventory Alerts */}
        <div className="polar-card p-4">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs font-mono uppercase tracking-wider font-semibold">Subsystem Health</span>
            <ShieldAlert className="w-4 h-4 text-rose-600" />
          </div>
          <div className="flex items-center gap-3">
            <div className="flex-1 bg-slate-50 p-2 rounded border border-slate-200 text-center">
              <span className="text-xs text-slate-500 font-mono block">Equip Warnings</span>
              <span className={`text-lg font-bold font-mono ${criticalEquipmentCount > 0 ? 'text-amber-600' : 'text-emerald-700'}`}>
                {criticalEquipmentCount}
              </span>
            </div>
            <div className="flex-1 bg-slate-50 p-2 rounded border border-slate-200 text-center">
              <span className="text-xs text-slate-500 font-mono block">Low Stock</span>
              <span className={`text-lg font-bold font-mono ${lowInventoryCount > 0 ? 'text-rose-600' : 'text-emerald-700'}`}>
                {lowInventoryCount}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Main Grid: Telemetry Trends & AI Recommendation Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols): Live Telemetry Charts & Warnings */}
        <div className="lg:col-span-2 space-y-6">
          {/* Telemetry Chart */}
          <div className="polar-card p-4">
            <div className="flex items-center justify-between mb-4 border-b border-slate-200 pb-2">
              <div>
                <h2 className="text-sm font-bold font-mono text-[#183153] uppercase tracking-wider flex items-center gap-2">
                  <Activity className="w-4 h-4 text-teal-600" />
                  Thermal & Energy Telemetry History
                </h2>
                <p className="text-xs text-slate-500 font-mono">Past 6 hours station microgrid load vs temperature</p>
              </div>
              <div className="flex items-center gap-3 text-xs font-mono">
                <span className="flex items-center gap-1.5 text-sky-600 font-semibold">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-600" /> Temp (°C)
                </span>
                <span className="flex items-center gap-1.5 text-teal-600 font-semibold">
                  <span className="w-2.5 h-2.5 rounded-full bg-teal-600" /> Load (kW)
                </span>
              </div>
            </div>

            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={mockTelemetryHistory} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="tempGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0284C7" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#0284C7" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="loadGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0D9488" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#0D9488" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                  <XAxis dataKey="time" stroke="#64748B" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '0.375rem', color: '#183153' }}
                  />
                  <Area type="monotone" dataKey="temp" stroke="#0284C7" fillOpacity={1} fill="url(#tempGrad)" strokeWidth={2} />
                  <Area type="monotone" dataKey="load" stroke="#0D9488" fillOpacity={1} fill="url(#loadGrad)" strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Subsystem Quick Status Row */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-mono">
            <div className="polar-card p-3 flex items-center gap-3">
              <div className="p-2 bg-emerald-50 text-emerald-700 rounded border border-emerald-200">
                <Zap className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs text-slate-500 block">Power Microgrid</span>
                <span className="text-xs font-bold text-slate-800">G1 + Solar Active</span>
              </div>
            </div>

            <div className="polar-card p-3 flex items-center gap-3">
              <div className="p-2 bg-amber-50 text-amber-700 rounded border border-amber-200">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs text-slate-500 block">HVAC Thermal Loop</span>
                <span className="text-xs font-bold text-amber-800">G2 Vibration Anomaly</span>
              </div>
            </div>

            <div className="polar-card p-3 flex items-center gap-3">
              <div className="p-2 bg-emerald-50 text-emerald-700 rounded border border-emerald-200">
                <Truck className="w-5 h-5" />
              </div>
              <div>
                <span className="text-xs text-slate-500 block">Resupply Status</span>
                <span className="text-xs font-bold text-slate-800">Vessel On Schedule</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column (1 col): AI Decision Feed (Human-in-the-Loop) */}
        <div className="polar-card p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between border-b border-slate-200 pb-2 mb-4">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-teal-600 animate-pulse" />
                <h2 className="text-sm font-bold font-mono text-[#183153] uppercase tracking-wider">
                  AI Decision Engine ("Sarthi")
                </h2>
              </div>
              <span className="text-[10px] px-2 py-0.5 bg-teal-50 text-teal-800 border border-teal-200 rounded font-mono font-bold">
                Human-in-Loop
              </span>
            </div>

            <p className="text-xs text-slate-500 font-mono mb-3">
              Predictive recommendations requiring NCPOR operator evaluation:
            </p>

            <div className="space-y-3 font-mono">
              {recommendations.map((rec) => (
                <div
                  key={rec.id}
                  className="bg-slate-50 border border-slate-200 rounded p-3 hover:border-slate-300 transition-colors"
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[11px] font-bold text-teal-700">{rec.id}</span>
                    <Badge status={rec.status} />
                  </div>
                  <h3 className="text-xs font-bold text-[#183153] mb-1">{rec.title}</h3>
                  <p className="text-[11px] text-slate-600 line-clamp-2 mb-2">{rec.description}</p>

                  <div className="flex items-center justify-between pt-1 border-t border-slate-200">
                    <span className="text-[10px] text-amber-700 font-semibold">Risk: {rec.risk}</span>
                    <button
                      onClick={() => setSelectedRec(rec)}
                      className="text-xs text-teal-700 hover:text-teal-900 font-semibold underline underline-offset-2"
                    >
                      Review Action →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-200 text-[10px] text-slate-500 font-mono flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Actions logged to NCPOR station operational audit file.</span>
          </div>
        </div>
      </div>

      {/* Reusable Recommendation Modal */}
      {selectedRec && (
        <RecommendationModal
          recommendation={selectedRec}
          onClose={() => setSelectedRec(null)}
        />
      )}
    </div>
  );
};
