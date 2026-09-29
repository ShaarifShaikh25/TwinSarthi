import React from 'react';
import { NavLink } from 'react-router-dom';
import { useStation } from '../../hooks/useStation';
import {
  LayoutDashboard,
  Box,
  Zap,
  Cpu,
  Truck,
  ShieldAlert,
  Sliders,
  Activity,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { recommendations, currentStation } = useStation();
  const pendingRecsCount = recommendations.filter((r) => r.status === 'PENDING').length;

  const navItems = [
    {
      path: '/',
      label: 'Mission Control',
      icon: LayoutDashboard,
      badge: null,
    },
    {
      path: '/digital-twin',
      label: 'Digital Twin',
      icon: Box,
      badge: '3D/2D',
    },
    {
      path: '/energy',
      label: 'Energy Microgrid',
      icon: Zap,
      badge: null,
    },
    {
      path: '/infrastructure',
      label: 'Infrastructure',
      icon: Cpu,
      badge: null,
    },
    {
      path: '/logistics',
      label: 'Logistics & Supply',
      icon: Truck,
      badge: null,
    },
    {
      path: '/risk-center',
      label: 'Risk Center',
      icon: ShieldAlert,
      badge: pendingRecsCount > 0 ? `${pendingRecsCount} Action` : null,
      badgeColor: 'bg-rose-100 text-rose-800 border border-rose-200',
    },
    {
      path: '/what-if',
      label: 'What-If Simulator',
      icon: Sliders,
      badge: 'Causal',
    },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 min-h-[calc(100vh-57px)]">
      {/* Primary Navigation Links */}
      <div className="p-3 space-y-1">
        <div className="px-3 py-2 text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
          Station Navigation
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center justify-between px-3 py-2.5 rounded-md text-xs font-mono transition-all ${
                  isActive
                    ? 'bg-teal-50 text-teal-800 border-l-4 border-l-teal-600 font-bold shadow-xs'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50 font-medium'
                }`
              }
            >
              <div className="flex items-center gap-2.5">
                <Icon className="w-4 h-4 text-teal-600" />
                <span>{item.label}</span>
              </div>

              {item.badge && (
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                    item.badgeColor || 'bg-slate-100 text-slate-700 border border-slate-200'
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Station Footer Summary */}
      <div className="p-3 border-t border-slate-200 bg-slate-50/80 font-mono text-[11px]">
        <div className="flex items-center justify-between text-slate-500 mb-1">
          <span className="flex items-center gap-1">
            <Activity className="w-3.5 h-3.5 text-emerald-600" />
            Active Station
          </span>
          <span className="text-[#183153] font-bold">{currentStation.name.split(' ')[0]}</span>
        </div>
        <div className="text-[10px] text-slate-500 leading-tight">
          {currentStation.location}
        </div>
        <div className="mt-2 text-[9px] text-slate-400 flex items-center justify-between border-t border-slate-200 pt-1.5">
          <span>Crew: {currentStation.crewCount} personnel</span>
          <span>NCPOR India</span>
        </div>
      </div>
    </aside>
  );
};
