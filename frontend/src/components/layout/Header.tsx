import React, { useState, useEffect } from 'react';
import { useStation } from '../../hooks/useStation';
import { DemoBadge } from '../ui/DemoBadge';
import { Badge } from '../ui/Badge';
import { formatTemp, getContinuityScoreColor } from '../../utils/formatters';
import { Radio, RefreshCw, Thermometer, Wind, Compass, Zap } from 'lucide-react';

export const Header: React.FC = () => {
  const {
    selectedStationId,
    setSelectedStationId,
    stations,
    currentStation,
    telemetry,
    connectionState,
    triggerSimulationEngine,
  } = useStation();

  const [utcTime, setUtcTime] = useState<string>('');
  const [isSimulating, setIsSimulating] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setUtcTime(
        new Date().toLocaleTimeString('en-GB', {
          timeZone: 'UTC',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        }) + ' UTC'
      );
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const handleSimulateClick = async () => {
    setIsSimulating(true);
    await triggerSimulationEngine();
    setTimeout(() => setIsSimulating(false), 1200);
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-[#DCE4ED] px-4 py-2.5 flex flex-wrap items-center justify-between gap-4 shadow-xs">
      {/* Brand & Station Selector */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-[#E8EEF5] text-[#0D9488] rounded border border-[#DCE4ED]">
            <Radio className="w-5 h-5 animate-pulse text-[#0D9488]" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-sm font-extrabold tracking-wider text-[#172B4D]">
                POLAR-TWIN
              </span>
              <span className="text-[10px] px-1.5 py-0.2 bg-[#E8EEF5] text-[#0D9488] font-bold rounded border border-[#DCE4ED]">
                NCPOR
              </span>
            </div>
            <p className="text-[10px] text-slate-500 font-mono">Antarctic Command Center</p>
          </div>
        </div>

        {/* Station Selector Buttons */}
        <div className="flex items-center bg-[#F1F5F9] p-1 rounded-md border border-[#DCE4ED] text-xs">
          {stations.map((st) => (
            <button
              key={st.id}
              onClick={() => setSelectedStationId(st.id)}
              className={`px-3 py-1 font-medium rounded transition-all flex items-center gap-1.5 ${
                selectedStationId === st.id
                  ? 'bg-[#0D9488] text-white shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              <Compass className="w-3.5 h-3.5" />
              {st.name.replace(' Research Station', '')}
              <Badge status={st.status} size="sm" />
            </button>
          ))}
        </div>
      </div>

      {/* Live Metrics Ticker */}
      <div className="hidden lg:flex items-center gap-5 bg-[#E8EEF5] px-4 py-1.5 rounded-md border border-[#DCE4ED] text-xs">
        <div className="flex items-center gap-1.5 text-slate-700">
          <Thermometer className="w-4 h-4 text-[#0D9488]" />
          <span className="text-slate-500 font-medium">Ambient:</span>
          <span className="font-bold text-[#172B4D] font-mono">{formatTemp(telemetry.temperature)}</span>
        </div>

        <div className="flex items-center gap-1.5 text-slate-700">
          <Wind className="w-4 h-4 text-[#38BDF8]" />
          <span className="text-slate-500 font-medium">Wind:</span>
          <span className="font-bold text-slate-800 font-mono">{telemetry.windSpeed || 42} km/h</span>
        </div>

        <div className="flex items-center gap-1.5 text-slate-700">
          <Zap className="w-4 h-4 text-[#F59E0B]" />
          <span className="text-slate-500 font-medium">Microgrid Fuel:</span>
          <span className="font-bold text-emerald-700 font-mono">{telemetry.fuel}%</span>
        </div>

        <div className="flex items-center gap-1.5 border-l border-[#DCE4ED] pl-4">
          <span className="text-slate-500 font-medium">Continuity:</span>
          <span className={`font-bold font-mono ${getContinuityScoreColor(currentStation.continuityScore)}`}>
            {currentStation.continuityScore}%
          </span>
        </div>
      </div>

      {/* Controls & Connection Badge */}
      <div className="flex items-center gap-3">
        {/* Connection status mode indicator */}
        {connectionState.mode === 'LIVE' ? (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono bg-emerald-50 text-emerald-800 border border-emerald-200 rounded font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-600 animate-ping" />
            WS LIVE
          </span>
        ) : (
          <DemoBadge label="DEMO MODE" tooltip="Backend WS offline. Using local Antarctic telemetry engine." />
        )}

        {/* Trigger Simulation POST /simulate */}
        <button
          onClick={handleSimulateClick}
          disabled={isSimulating}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-[#E8EEF5] hover:bg-slate-200 text-[#172B4D] border border-[#DCE4ED] rounded text-xs font-semibold transition-colors"
          title="Triggers FastAPI POST /simulate endpoint"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-[#0D9488] ${isSimulating ? 'animate-spin' : ''}`} />
          Run Simulation Engine
        </button>

        {/* UTC Clock */}
        <div className="hidden sm:block text-xs font-mono text-slate-600 bg-[#E8EEF5] px-2.5 py-1 rounded border border-[#DCE4ED] font-semibold">
          {utcTime || '00:00:00 UTC'}
        </div>
      </div>
    </header>
  );
};
