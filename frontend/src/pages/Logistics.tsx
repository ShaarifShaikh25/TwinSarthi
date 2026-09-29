import React from 'react';
import { useStation } from '../hooks/useStation';
import { Badge } from '../components/ui/Badge';
import { Truck, Package, AlertTriangle, Calendar } from 'lucide-react';

export const Logistics: React.FC = () => {
  const { inventory } = useStation();

  const lowStockItems = inventory.filter((i) => i.resupplyStatus !== 'Sufficient');

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-[#183153] font-mono tracking-tight flex items-center gap-2">
              <Truck className="w-5 h-5 text-emerald-700" />
              STATION LOGISTICS & RESUPPLY CONTROL
            </h1>
            <Badge status="NORMAL" label="Resupply Tracking Active" />
          </div>
          <p className="text-xs text-slate-500 font-mono mt-1">
            Fuel reserves, freeze-dried rations, emergency surgical kits & critical replacement spare parts
          </p>
        </div>

        <div className="text-xs font-mono text-slate-600 bg-white px-3 py-1.5 rounded border border-slate-200 shadow-xs flex items-center gap-2">
          <Calendar className="w-4 h-4 text-teal-600" />
          MV Vasiliy Golovnin Arrival: <span className="text-teal-700 font-bold">42 Days Countdown</span>
        </div>
      </div>

      {/* Stockout Warning Alert Banner */}
      {lowStockItems.length > 0 && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-center justify-between gap-4 shadow-xs">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 text-amber-800 rounded border border-amber-300">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold font-mono text-amber-900 uppercase tracking-wider">
                Predicted Stockout Warning ({lowStockItems.length} Items Require Priority Resupply)
              </h3>
              <p className="text-xs text-amber-800 font-mono mt-0.5">
                {lowStockItems.map((i) => `${i.name} (${i.daysRemaining} days remaining)`).join(' • ')}
              </p>
            </div>
          </div>
          <span className="text-xs font-mono px-3 py-1 bg-amber-600 text-white font-bold rounded">
            NCPOR Manifest Alert
          </span>
        </div>
      )}

      {/* Inventory Items Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 font-mono">
        {inventory.map((item) => (
          <div key={item.id} className="polar-card p-4 flex flex-col justify-between space-y-3">
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] text-teal-700 font-bold uppercase tracking-wider">{item.category}</span>
                <Badge status={item.resupplyStatus} />
              </div>

              <h3 className="text-xs font-bold text-[#183153] mb-1">{item.name}</h3>
              <span className="text-[10px] text-slate-500 block mb-3">ID: {item.id}</span>

              <div className="bg-slate-50 p-3 rounded border border-slate-200 space-y-2 text-xs">
                <div className="flex justify-between items-baseline">
                  <span className="text-slate-500">Current Stock:</span>
                  <span className="text-base font-extrabold text-[#183153]">
                    {item.quantity.toLocaleString()} {item.unit}
                  </span>
                </div>

                <div className="flex justify-between text-[11px] text-slate-500 border-t border-slate-200 pt-1.5">
                  <span>Burn Rate:</span>
                  <span className="text-amber-700 font-semibold">{item.consumptionRatePerDay} {item.unit}/Day</span>
                </div>

                <div className="flex justify-between text-[11px] text-slate-500">
                  <span>Days Remaining:</span>
                  <span className={`font-bold ${item.daysRemaining < 60 ? 'text-amber-700' : 'text-emerald-700'}`}>
                    ~{item.daysRemaining} Days
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 text-[10px] text-slate-500 flex items-center justify-between">
              <span>Predicted Stockout:</span>
              <span className="text-slate-800 font-bold">{item.predictedStockoutDate}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Resupply Logistics Summary Card */}
      <div className="polar-card p-5 space-y-3 font-mono">
        <h3 className="text-xs font-bold text-[#183153] uppercase tracking-wider flex items-center gap-2">
          <Package className="w-4 h-4 text-teal-600" />
          Antarctic Seasonal Resupply Vessel Overview (NCPOR Logistics Manifest)
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
          <div className="bg-slate-50 p-3 rounded border border-slate-200">
            <span className="text-slate-500 text-[10px] block">Vessel Name</span>
            <span className="text-teal-800 font-bold">MV Vasiliy Golovnin</span>
          </div>
          <div className="bg-slate-50 p-3 rounded border border-slate-200">
            <span className="text-slate-500 text-[10px] block">Departure Port</span>
            <span className="text-slate-800 font-medium">Cape Town, South Africa</span>
          </div>
          <div className="bg-slate-50 p-3 rounded border border-slate-200">
            <span className="text-slate-500 text-[10px] block">ETA At Maitri / Bharati</span>
            <span className="text-emerald-700 font-bold">November 10, 2026</span>
          </div>
          <div className="bg-slate-50 p-3 rounded border border-slate-200">
            <span className="text-slate-500 text-[10px] block">Unlading Payload</span>
            <span className="text-teal-700 font-bold">450,000 L Fuel + Provisions</span>
          </div>
        </div>
      </div>
    </div>
  );
};
