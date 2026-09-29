import React, { useState } from 'react';
import { useStation } from '../hooks/useStation';
import { Equipment } from '../types';
import { Badge } from '../components/ui/Badge';
import { Cpu, Filter, CheckCircle2, ChevronRight } from 'lucide-react';

export const Infrastructure: React.FC = () => {
  const { equipment } = useStation();
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [inspectEquipment, setInspectEquipment] = useState<Equipment | null>(equipment[0]);

  const categories = ['ALL', 'Generator', 'HVAC', 'Water', 'Wastewater', 'Communications', 'Fuel Depot'];
  const statuses = ['ALL', 'NORMAL', 'WARNING', 'CRITICAL'];

  const filteredEquipment = equipment.filter((e) => {
    const matchesCategory = selectedCategory === 'ALL' || e.category === selectedCategory;
    const matchesStatus = selectedStatus === 'ALL' || e.status === selectedStatus;
    return matchesCategory && matchesStatus;
  });

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-[#183153] font-mono tracking-tight flex items-center gap-2">
              <Cpu className="w-5 h-5 text-teal-600" />
              STATION INFRASTRUCTURE & SUBSYSTEMS
            </h1>
            <Badge status="NORMAL" label="8 Subsystems Online" />
          </div>
          <p className="text-xs text-slate-500 font-mono mt-1">
            Generators, HVAC thermal loops, sub-glacial meltwater intake, wastewater bioreactors & satellite ground stations
          </p>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="polar-card p-4 flex flex-wrap items-center justify-between gap-4 font-mono text-xs">
        {/* Category Filters */}
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-slate-500 flex items-center gap-1 font-semibold">
            <Filter className="w-3.5 h-3.5 text-teal-600" /> Subsystem:
          </span>
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded transition-colors ${
                selectedCategory === cat
                  ? 'bg-teal-600 text-white font-bold shadow-xs'
                  : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200 font-medium'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Status Filters */}
        <div className="flex items-center gap-2">
          <span className="text-slate-500 font-semibold">Status:</span>
          {statuses.map((st) => (
            <button
              key={st}
              onClick={() => setSelectedStatus(st)}
              className={`px-2.5 py-1 rounded transition-colors ${
                selectedStatus === st
                  ? 'bg-teal-600 text-white font-bold shadow-xs'
                  : 'bg-white text-slate-600 hover:text-slate-900 border border-slate-200 font-medium'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Grid: Equipment Table & Inspection Detail Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols): Equipment List */}
        <div className="lg:col-span-2 polar-card p-4 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse font-mono text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-[#183153] uppercase text-[10px] tracking-wider font-bold bg-slate-50">
                  <th className="p-3">ID & Component</th>
                  <th className="p-3">Category</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Health</th>
                  <th className="p-3">Maintenance Due</th>
                  <th className="p-3 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {filteredEquipment.map((eq) => (
                  <tr
                    key={eq.id}
                    onClick={() => setInspectEquipment(eq)}
                    className={`hover:bg-slate-50 cursor-pointer transition-colors ${
                      inspectEquipment?.id === eq.id ? 'bg-teal-50/50 font-semibold' : ''
                    }`}
                  >
                    <td className="p-3">
                      <span className="text-teal-700 font-bold block">{eq.id}</span>
                      <span className="text-slate-500 text-[11px] truncate block max-w-xs">{eq.name}</span>
                    </td>
                    <td className="p-3 text-slate-600">{eq.category}</td>
                    <td className="p-3">
                      <Badge status={eq.status} />
                    </td>
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                          <div
                            className={`h-full ${
                              eq.health > 80 ? 'bg-emerald-600' : eq.health > 60 ? 'bg-amber-600' : 'bg-rose-600'
                            }`}
                            style={{ width: `${eq.health}%` }}
                          />
                        </div>
                        <span className="font-bold text-[#183153]">{eq.health}%</span>
                      </div>
                    </td>
                    <td className="p-3 text-slate-500">{eq.nextMaintenance}</td>
                    <td className="p-3 text-right">
                      <ChevronRight className="w-4 h-4 text-teal-600 inline-block" />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right Column (1 col): Selected Equipment Detail Card */}
        {inspectEquipment && (
          <div className="polar-card p-5 space-y-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between border-b border-slate-200 pb-3 mb-4">
                <div>
                  <span className="text-[10px] font-mono text-teal-700 uppercase tracking-wider block font-semibold">
                    Maintenance Detail Panel
                  </span>
                  <h3 className="text-base font-bold font-mono text-[#183153]">{inspectEquipment.id}</h3>
                </div>
                <Badge status={inspectEquipment.status} size="md" />
              </div>

              <div className="space-y-4 font-mono text-xs">
                <div>
                  <span className="text-slate-500 block text-[10px] uppercase mb-1 font-semibold">Description</span>
                  <p className="bg-slate-50 p-2.5 rounded border border-slate-200 text-[#183153]">
                    {inspectEquipment.name}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
                    <span className="text-slate-500 text-[10px] block">Location</span>
                    <span className="text-teal-800 font-semibold">{inspectEquipment.location}</span>
                  </div>
                  <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
                    <span className="text-slate-500 text-[10px] block">Risk Rating</span>
                    <span className={`font-bold ${inspectEquipment.riskLevel === 'HIGH' ? 'text-rose-600' : 'text-emerald-700'}`}>
                      {inspectEquipment.riskLevel}
                    </span>
                  </div>
                </div>

                <div>
                  <span className="text-slate-500 block text-[10px] uppercase mb-1 font-semibold">System Parameters</span>
                  <div className="bg-white p-3 rounded border border-slate-200 space-y-1.5">
                    {Object.entries(inspectEquipment.specs).map(([k, v]) => (
                      <div key={k} className="flex justify-between border-b border-slate-100 pb-1">
                        <span className="text-slate-500">{k}:</span>
                        <span className="text-teal-800 font-semibold">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-50 p-3 rounded border border-slate-200 space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Last Overhaul:</span>
                    <span className="text-slate-700">{inspectEquipment.lastMaintenance}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Next Overhaul:</span>
                    <span className="text-amber-700 font-bold">{inspectEquipment.nextMaintenance}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-200 text-[10px] text-slate-500 font-mono flex items-center justify-between">
              <span>Subsystem: {inspectEquipment.subsystemId}</span>
              <span className="text-emerald-700 flex items-center gap-1 font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5" /> Sensor Verified
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
