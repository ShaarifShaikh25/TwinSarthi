import React, { useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import { useStation } from '../hooks/useStation';
import { Equipment } from '../types';
import { Badge } from '../components/ui/Badge';
import { ErrorBoundary } from '../components/ui/ErrorBoundary';
import { Box, Layers, Eye, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';

// WebGL availability detection helper
function isWebGLAvailable(): boolean {
  try {
    const canvas = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
  } catch {
    return false;
  }
}

// 3D Station Module Box representation
const Station3DModule: React.FC<{
  position: [number, number, number];
  color: string;
  label: string;
  status: string;
  isSelected: boolean;
  onClick: () => void;
}> = ({ position, color, label, status, isSelected, onClick }) => {
  return (
    <group position={position} onClick={onClick}>
      {/* Station Building Block */}
      <mesh castShadow receiveShadow>
        <boxGeometry args={[2.5, 1.2, 1.8]} />
        <meshStandardMaterial
          color={isSelected ? '#0D9488' : color}
          metalness={0.2}
          roughness={0.4}
          wireframe={isSelected}
        />
      </mesh>

      {/* Building Base outline */}
      <mesh position={[0, -0.65, 0]}>
        <boxGeometry args={[2.7, 0.1, 2.0]} />
        <meshStandardMaterial color="#CBD5E1" />
      </mesh>

      {/* Status LED Beacon */}
      <mesh position={[1.0, 0.7, 0.7]}>
        <sphereGeometry args={[0.15, 16, 16]} />
        <meshBasicMaterial
          color={status === 'CRITICAL' ? '#EF6461' : status === 'WARNING' ? '#F59E0B' : '#15803D'}
        />
      </mesh>

      {/* HTML Label Floating Above */}
      <Html position={[0, 1.1, 0]} center distanceFactor={12}>
        <div
          className={`px-2 py-0.5 rounded text-[10px] font-mono whitespace-nowrap cursor-pointer transition-all ${
            isSelected
              ? 'bg-[#0D9488] text-white font-bold shadow-md scale-110'
              : 'bg-white/95 text-[#1E293B] border border-slate-300 font-semibold shadow-xs'
          }`}
        >
          {label}
        </div>
      </Html>
    </group>
  );
};

export const DigitalTwin: React.FC = () => {
  const { equipment, telemetry } = useStation();
  const webGLSupported = isWebGLAvailable();
  const [viewMode, setViewMode] = useState<'3D' | '2D'>(webGLSupported ? '3D' : '2D');
  const [selectedEquipmentId, setSelectedEquipmentId] = useState<string>('GEN-01');

  const selectedEquipment: Equipment =
    equipment.find((e) => e.id === selectedEquipmentId) || equipment[0];

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[#DCE4ED] pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-[#1E293B] tracking-tight flex items-center gap-2">
              <Box className="w-5 h-5 text-[#0D9488]" />
              DIGITAL TWIN — 3D/2D SCHEMATIC INTERFACE
            </h1>
            <Badge status="NORMAL" label="Live Telemetry Sync" />
          </div>
          <p className="text-xs text-[#64748B] mt-1">
            Real-time Antarctic research station module visual twin & sensor telemetry mapping
          </p>
        </div>

        {/* View Mode Toggle: 3D vs 2D Fallback */}
        <div className="flex items-center bg-[#E8EEF5] p-1 rounded-md border border-[#DCE4ED] text-xs">
          <button
            onClick={() => setViewMode('3D')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
              viewMode === '3D' ? 'bg-[#0D9488] text-white font-bold shadow-xs' : 'text-[#64748B] hover:text-[#1E293B]'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            3D Canvas
          </button>
          <button
            onClick={() => setViewMode('2D')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
              viewMode === '2D' ? 'bg-[#0D9488] text-white font-bold shadow-xs' : 'text-[#64748B] hover:text-[#1E293B]'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            2D Schematic View
          </button>
        </div>
      </div>

      {/* Main Twin Viewport & Equipment Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column (2 cols): 3D Viewport / 2D Fallback */}
        <div className="lg:col-span-2 polar-card p-2 relative h-[520px] rounded-lg overflow-hidden flex flex-col justify-between">
          {viewMode === '3D' && webGLSupported ? (
            <div className="w-full h-full bg-[#F1F5F9] rounded overflow-hidden relative border border-[#DCE4ED]">
              <ErrorBoundary
                fallback={
                  <div className="p-6 text-center text-[#1E293B] space-y-3">
                    <AlertTriangle className="w-8 h-8 text-[#F59E0B] mx-auto" />
                    <p className="text-xs font-bold text-amber-800">WebGL Hardware Render Interrupted</p>
                    <p className="text-xs text-[#64748B]">Switched to 2D Polar Station Architectural Layout fallback.</p>
                    <button
                      onClick={() => setViewMode('2D')}
                      className="px-4 py-1.5 bg-[#0D9488] text-white font-bold text-xs rounded"
                    >
                      Switch to 2D Schematic Mode
                    </button>
                  </div>
                }
              >
                <Canvas camera={{ position: [6, 8, 10], fov: 45 }}>
                  <ambientLight intensity={0.9} />
                  <directionalLight position={[10, 15, 5]} intensity={1.4} castShadow />
                  <pointLight position={[-10, 10, -10]} intensity={0.6} />

                  {/* Ground Plane */}
                  <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.7, 0]} receiveShadow>
                    <planeGeometry args={[40, 40]} />
                    <meshStandardMaterial color="#CBD5E1" roughness={0.9} />
                  </mesh>

                  {/* 3D Station Buildings */}
                  <Suspense fallback={null}>
                    <Station3DModule
                      position={[-3, 0, 0]}
                      color="#38BDF8"
                      label="Habitation Module"
                      status="NORMAL"
                      isSelected={selectedEquipmentId === 'HVAC-01'}
                      onClick={() => setSelectedEquipmentId('HVAC-01')}
                    />
                    <Station3DModule
                      position={[0, 0, 0]}
                      color="#F59E0B"
                      label="Power House G1-G4"
                      status="WARNING"
                      isSelected={selectedEquipmentId === 'GEN-01' || selectedEquipmentId === 'GEN-02'}
                      onClick={() => setSelectedEquipmentId('GEN-01')}
                    />
                    <Station3DModule
                      position={[3, 0, 0]}
                      color="#EF6461"
                      label="Science Lab Module"
                      status="CRITICAL"
                      isSelected={selectedEquipmentId === 'HVAC-02'}
                      onClick={() => setSelectedEquipmentId('HVAC-02')}
                    />
                    <Station3DModule
                      position={[0, 0, -3.5]}
                      color="#15803D"
                      label="Exterior Fuel Depot"
                      status="NORMAL"
                      isSelected={selectedEquipmentId === 'FUEL-01'}
                      onClick={() => setSelectedEquipmentId('FUEL-01')}
                    />
                    <Station3DModule
                      position={[-3, 0, -3.5]}
                      color="#38BDF8"
                      label="Meltwater Intake"
                      status="NORMAL"
                      isSelected={selectedEquipmentId === 'WTR-01'}
                      onClick={() => setSelectedEquipmentId('WTR-01')}
                    />
                    <Station3DModule
                      position={[3, 0, -3.5]}
                      color="#0D9488"
                      label="Satellite Radome"
                      status="NORMAL"
                      isSelected={selectedEquipmentId === 'COM-01'}
                      onClick={() => setSelectedEquipmentId('COM-01')}
                    />
                  </Suspense>

                  <OrbitControls enablePan enableZoom maxPolarAngle={Math.PI / 2.1} />
                </Canvas>
              </ErrorBoundary>

              {/* Viewport Control Instructions */}
              <div className="absolute bottom-3 left-3 bg-white/90 px-3 py-1.5 rounded border border-[#DCE4ED] text-[11px] text-[#64748B] shadow-xs pointer-events-none font-mono">
                Mouse Drag: Rotate | Scroll: Zoom | Click module to inspect
              </div>
            </div>
          ) : (
            /* 2D Schematic View Fallback */
            <div className="w-full h-full bg-[#F8FAFC] p-4 rounded overflow-auto border border-[#DCE4ED]">
              <div className="text-xs font-bold text-[#0D9488] mb-4 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4" /> 2D Polar Station Architectural Layout
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {equipment.map((eq) => (
                  <button
                    key={eq.id}
                    onClick={() => setSelectedEquipmentId(eq.id)}
                    className={`p-4 rounded border text-left transition-all ${
                      selectedEquipmentId === eq.id
                        ? 'bg-white border-[#0D9488] shadow-sm ring-1 ring-[#0D9488]'
                        : 'bg-white border-[#DCE4ED] hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-[#1E293B] font-mono">{eq.id}</span>
                      <Badge status={eq.status} />
                    </div>
                    <h4 className="text-xs text-[#0D9488] font-semibold mb-1 truncate">{eq.name}</h4>
                    <p className="text-[10px] text-[#64748B]">{eq.location}</p>
                    <div className="mt-3 flex items-center justify-between text-[11px] border-t border-[#DCE4ED] pt-2">
                      <span className="text-[#64748B]">Health:</span>
                      <span className="font-bold text-[#15803D] font-mono">{eq.health}%</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column (1 col): Selected Subsystem Equipment Details Panel (Deep Navy Panel) */}
        <div className="polar-panel-navy p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between border-b border-[#2A4365] pb-3 mb-4">
              <div>
                <span className="text-[10px] font-mono text-[#38BDF8] uppercase tracking-wider block font-bold">
                  Equipment Telemetry Panel
                </span>
                <h3 className="text-base font-bold font-mono text-white">{selectedEquipment.id}</h3>
              </div>
              <Badge status={selectedEquipment.status} size="md" />
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-slate-300 block mb-0.5 font-medium">Component Title</label>
                <p className="text-xs font-bold text-[#38BDF8] font-mono bg-[#0F1C33] p-2.5 rounded border border-[#2A4365]">
                  {selectedEquipment.name}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 text-xs">
                <div className="bg-[#0F1C33] p-2.5 rounded border border-[#2A4365]">
                  <span className="text-slate-400 block text-[10px]">Category</span>
                  <span className="text-slate-200 font-semibold">{selectedEquipment.category}</span>
                </div>
                <div className="bg-[#0F1C33] p-2.5 rounded border border-[#2A4365]">
                  <span className="text-slate-400 block text-[10px]">Health Score</span>
                  <span className={`font-bold font-mono ${selectedEquipment.health > 80 ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {selectedEquipment.health}%
                  </span>
                </div>
              </div>

              <div>
                <label className="text-xs text-slate-300 block mb-1 font-medium">Live Sensor Telemetry</label>
                <div className="bg-[#0B1526] p-3 rounded border border-[#2A4365] text-xs space-y-2">
                  {Object.entries(selectedEquipment.specs).map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b border-slate-800/80 pb-1 text-xs">
                      <span className="text-slate-400">{k}:</span>
                      <span className="text-cyan-300 font-mono font-semibold">{v}</span>
                    </div>
                  ))}
                  <div className="flex justify-between text-xs pt-1">
                    <span className="text-slate-400">Ambient Temp:</span>
                    <span className="text-teal-400 font-mono font-semibold">{telemetry.temperature}°C</span>
                  </div>
                </div>
              </div>

              <div className="bg-[#0F1C33] p-3 rounded border border-[#2A4365] text-xs space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-400">Last Service:</span>
                  <span className="text-slate-300 font-mono">{selectedEquipment.lastMaintenance}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Next Service Due:</span>
                  <span className="text-amber-400 font-mono font-semibold">{selectedEquipment.nextMaintenance}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="text-[10px] text-slate-400 border-t border-[#2A4365] pt-3 flex items-center justify-between">
            <span className="font-mono">Subsystem ID: {selectedEquipment.subsystemId}</span>
            <span className="text-cyan-400 flex items-center gap-1 font-semibold">
              <ShieldCheck className="w-3.5 h-3.5" /> Sensor Verified
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DigitalTwin;
