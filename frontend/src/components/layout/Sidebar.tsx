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
      badgeColor: 'bg-rose-50 text-rose-800 border border-rose-200',
    },
    {
      path: '/what-if',
      label: 'What-If Simulator',
      icon: Sliders,
      badge: 'Causal',
    },
  ];

  return (
    <aside className="w-64 bg-white border-r border-[#DCE4ED] flex flex-col justify-between shrink-0 min-h-[calc(100vh-57px)]">
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
                `flex items-center justify-between px-3 py-2.5 rounded-md text-xs transition-all ${
                  isActive
                    ? 'bg-[#E8EEF5] text-[#0D9488] border-l-4 border-l-[#0D9488] font-bold shadow-xs'
                    : 'text-slate-600 hover:text-[#172B4D] hover:bg-slate-50 font-medium'
                }`
              }
            >
              <div className="flex items-center gap-2.5">
                <Icon className="w-4 h-4 text-[#0D9488]" />
                <span>{item.label}</span>
              </div>

              {item.badge && (
                <span
                  className={`text-[10px] px-1.5 py-0.5 rounded font-bold font-mono ${
                    item.badgeColor || 'bg-[#E8EEF5] text-slate-700 border border-[#DCE4ED]'
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
      <div className="p-3 border-t border-[#DCE4ED] bg-[#F8FAFC] text-[11px]">
        <div className="flex items-center justify-between text-slate-500 mb-1">
          <span className="flex items-center gap-1">
            <Activity className="w-3.5 h-3.5 text-emerald-700" />
            Active Station
          </span>
          <span className="text-[#172B4D] font-bold">{currentStation.name.split(' ')[0]}</span>
        </div>
        <div className="text-[10px] text-slate-500 leading-tight">
          {currentStation.location}
        </div>
        <div className="mt-2 text-[9px] text-slate-400 flex items-center justify-between border-t border-[#DCE4ED] pt-1.5 font-mono">
          <span>Crew: {currentStation.crewCount} personnel</span>
          <span>NCPOR India</span>
        </div>
      </div>
    </aside>
  );
};
