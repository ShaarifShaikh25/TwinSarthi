import React from 'react';
import { useStation } from '../hooks/useStation';
import { Badge } from '../components/ui/Badge';
import { Zap, Battery, Flame, Sun, TrendingDown } from 'lucide-react';
import {
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

const energyHistoryAndForecast = [
  { day: 'Day -5', actualFuel: 94.0, forecastFuel: null, powerKw: 110, solarKw: 45 },
  { day: 'Day -4', actualFuel: 92.5, forecastFuel: null, powerKw: 112, solarKw: 42 },
  { day: 'Day -3', actualFuel: 90.8, forecastFuel: null, powerKw: 118, solarKw: 38 },
  { day: 'Day -2', actualFuel: 89.0, forecastFuel: null, powerKw: 125, solarKw: 30 },
  { day: 'Day -1', actualFuel: 87.4, forecastFuel: null, powerKw: 130, solarKw: 25 },
  { day: 'Today', actualFuel: 86.0, forecastFuel: 86.0, powerKw: 108, solarKw: 38 },
  { day: 'Day +1 (Fcst)', actualFuel: null, forecastFuel: 84.2, powerKw: 112, solarKw: 35 },
  { day: 'Day +2 (Fcst)', actualFuel: null, forecastFuel: 82.5, powerKw: 115, solarKw: 32 },
  { day: 'Day +3 (Fcst)', actualFuel: null, forecastFuel: 80.7, powerKw: 118, solarKw: 30 },
  { day: 'Day +5 (Fcst)', actualFuel: null, forecastFuel: 77.0, powerKw: 120, solarKw: 28 },
  { day: 'Day +7 (Fcst)', actualFuel: null, forecastFuel: 73.2, powerKw: 122, solarKw: 25 },
];

export const Energy: React.FC = () => {
  const { telemetry, inventory } = useStation();

  const fuelItem = inventory.find((i) => i.category === 'Fuel') || inventory[0];
  const fuelLiters = fuelItem.quantity;
  const burnRate = fuelItem.consumptionRatePerDay;
  const daysRemaining = fuelItem.daysRemaining;

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-[#183153] font-mono tracking-tight flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-600" />
              ENERGY & MICROGRID MANAGEMENT
            </h1>
            <Badge status="NORMAL" label="Microgrid Stable" />
          </div>
          <p className="text-xs text-slate-500 font-mono mt-1">
            Diesel generator dispatch, solar photovoltaic yield, battery energy storage & fuel forecasts
          </p>
        </div>

        <div className="text-xs font-mono text-slate-600 bg-white px-3 py-1.5 rounded border border-slate-200 shadow-xs">
          Estimated Buffer: <span className="text-emerald-700 font-bold">{daysRemaining} Days Operational</span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 font-mono">
        {/* Total Station Power Consumption */}
        <div className="polar-card p-4">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold">Station Microgrid Load</span>
            <Zap className="w-4 h-4 text-teal-600" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold font-mono text-[#183153]">
              {telemetry.generatorKw || 110} kW
            </span>
            <span className="text-xs text-emerald-700 font-bold">92.4% Duty</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Generator G1 + BESS Peak Buffer
          </p>
        </div>

        {/* Diesel Generator Load Pct */}
        <div className="polar-card p-4">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold">Generator G1 Output</span>
            <Flame className="w-4 h-4 text-amber-600" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold font-mono text-amber-700">
              68.5%
            </span>
            <span className="text-xs text-slate-600 font-semibold">170 kVA Output</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Cummins 250kVA Polar Specs
          </p>
        </div>

        {/* Battery Storage BESS */}
        <div className="polar-card p-4">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold">Battery BESS Charge</span>
            <Battery className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold font-mono text-emerald-700">
              {telemetry.batteryPct || 86}%
            </span>
            <span className="text-xs text-slate-600 font-semibold">240 kWh Available</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Discharge Autonomy: ~14 Hours
          </p>
        </div>

        {/* Solar Photovoltaic Yield */}
        <div className="polar-card p-4">
          <div className="flex items-center justify-between text-slate-500 mb-2">
            <span className="text-xs uppercase tracking-wider font-semibold">Solar Array Output</span>
            <Sun className="w-4 h-4 text-amber-500" />
          </div>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold font-mono text-teal-700">
              {telemetry.solarKw || 38.5} kW
            </span>
            <span className="text-xs text-teal-800 font-semibold">+28.5% Offset</span>
          </div>
          <p className="text-[11px] text-slate-500 mt-2">
            Polar Solar Tilt: 72° South
          </p>
        </div>
      </div>

      {/* Main Chart Section: Historical vs AI Forecast */}
      <div className="polar-card p-5 space-y-4">
        <div className="flex flex-wrap items-center justify-between border-b border-slate-200 pb-3 gap-2">
          <div>
            <h2 className="text-sm font-bold font-mono text-[#183153] uppercase tracking-wider flex items-center gap-2">
              <TrendingDown className="w-4 h-4 text-teal-600" />
              Fuel Reserve Depletion & Demand Forecast Model
            </h2>
            <p className="text-xs text-slate-500 font-mono">
              Historical measurements (solid line) vs 7-day predictive forecast model (dashed line)
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5 text-emerald-700 font-semibold">
              <span className="w-3 h-0.5 bg-emerald-700" /> Historical Fuel %
            </span>
            <span className="flex items-center gap-1.5 text-amber-600 font-semibold">
              <span className="w-3 h-0.5 border-t-2 border-dashed border-amber-600" /> AI Forecast Fuel %
            </span>
            <span className="flex items-center gap-1.5 text-teal-600 font-semibold">
              <span className="w-3 h-0.5 bg-teal-600" /> Microgrid Load (kW)
            </span>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={energyHistoryAndForecast} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="day" stroke="#64748B" fontSize={11} tickLine={false} />
              <YAxis stroke="#64748B" fontSize={11} tickLine={false} />
              <Tooltip
                contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '0.375rem', color: '#183153' }}
              />
              <Legend />
              {/* Historical Fuel Line */}
              <Line
                type="monotone"
                dataKey="actualFuel"
                name="Historical Fuel (%)"
                stroke="#15803D"
                strokeWidth={3}
                dot={{ r: 4, fill: '#15803D' }}
              />
              {/* Predictive Forecast Line */}
              <Line
                type="monotone"
                dataKey="forecastFuel"
                name="AI Forecast Fuel (%)"
                stroke="#D97706"
                strokeWidth={3}
                strokeDasharray="5 5"
                dot={{ r: 4, fill: '#D97706' }}
              />
              {/* Power Load Bar / Line */}
              <Line
                type="monotone"
                dataKey="powerKw"
                name="Microgrid Load (kW)"
                stroke="#0D9488"
                strokeWidth={2}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Burn Rate Calculator Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono">
        <div className="polar-card p-4">
          <span className="text-xs text-slate-500 block mb-1">Current Fuel Storage</span>
          <span className="text-2xl font-bold text-[#183153]">{fuelLiters.toLocaleString()} Liters</span>
          <p className="text-[11px] text-slate-500 mt-1">Primary Tank Matrix 1-4</p>
        </div>

        <div className="polar-card p-4">
          <span className="text-xs text-slate-500 block mb-1">Average Daily Burn Rate</span>
          <span className="text-2xl font-bold text-amber-700">{burnRate} L/Day</span>
          <p className="text-[11px] text-slate-500 mt-1">Based on past 30 days telemetry</p>
        </div>

        <div className="polar-card p-4">
          <span className="text-xs text-slate-500 block mb-1">NCPOR Safety Buffer Minimum</span>
          <span className="text-2xl font-bold text-emerald-700">30,000 Liters</span>
          <p className="text-[11px] text-emerald-700 mt-1">Resupply window buffer compliant</p>
        </div>
      </div>
    </div>
  );
};
