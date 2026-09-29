import React, { useState, Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Html } from '@react-three/drei';
import { useStation } from '../hooks/useStation';
import { Equipment } from '../types';
import { Badge } from '../components/ui/Badge';
import { ErrorBoundary } from '../components/ui/ErrorBoundary';
import { Box, Layers, Eye, AlertTriangle } from 'lucide-react';

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
          color={status === 'CRITICAL' ? '#DC2626' : status === 'WARNING' ? '#D97706' : '#15803D'}
        />
      </mesh>

      {/* HTML Label Floating Above */}
      <Html position={[0, 1.1, 0]} center distanceFactor={12}>
        <div
          className={`px-2 py-0.5 rounded text-[10px] font-mono whitespace-nowrap cursor-pointer transition-all ${
            isSelected
              ? 'bg-teal-600 text-white font-bold shadow-md scale-110'
              : 'bg-white/95 text-[#183153] border border-slate-300 font-semibold shadow-xs'
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
  const [viewMode, setViewMode] = useState<'3D' | '2D'>('3D');
  const [selectedEquipmentId, setSelectedEquipmentId] = useState<string>('GEN-01');

  const selectedEquipment: Equipment =
    equipment.find((e) => e.id === selectedEquipmentId) || equipment[0];

  return (
    <div className="p-4 lg:p-6 space-y-6">
      {/* Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-[#183153] font-mono tracking-tight flex items-center gap-2">
              <Box className="w-5 h-5 text-teal-600" />
              DIGITAL TWIN — 3D/2D SCHEMATIC INTERFACE
            </h1>
            <Badge status="NORMAL" label="Live Telemetry Sync" />
          </div>
          <p className="text-xs text-slate-500 font-mono mt-1">
            Real-time Antarctic research station module visual twin & sensor telemetry mapping
          </p>
        </div>

        {/* View Mode Toggle: 3D vs 2D Fallback */}
        <div className="flex items-center bg-slate-100 p-1 rounded-md border border-slate-200 font-mono text-xs">
          <button
            onClick={() => setViewMode('3D')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
              viewMode === '3D' ? 'bg-teal-600 text-white font-bold shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            3D Canvas
          </button>
          <button
            onClick={() => setViewMode('2D')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded transition-colors ${
              viewMode === '2D' ? 'bg-teal-600 text-white font-bold shadow-xs' : 'text-slate-600 hover:text-slate-900'
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
          {viewMode === '3D' ? (
            <div className="w-full h-full bg-[#F1F5F9] rounded overflow-hidden relative border border-slate-200">
              <ErrorBoundary
                fallback={
                  <div className="p-6 text-center text-slate-700 font-mono space-y-3">
                    <AlertTriangle className="w-8 h-8 text-amber-600 mx-auto" />
                    <p className="text-xs font-bold text-amber-800">WebGL Hardware Acceleration Unavailable</p>
                    <p className="text-xs text-slate-500">Showing 2D Polar Station Architectural Layout fallback.</p>
                    <button
                      onClick={() => setViewMode('2D')}
                      className="px-4 py-1.5 bg-teal-600 text-white font-bold text-xs rounded"
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

                  {/* Snow Ground Plane */}
                  <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.7, 0]} receiveShadow>
                    <planeGeometry args={[40, 40]} />
                    <meshStandardMaterial color="#E2E8F0" roughness={0.9} />
                  </mesh>

                  {/* 3D Station Buildings */}
                  <Suspense fallback={null}>
                    <Station3DModule
                      position={[-3, 0, 0]}
                      color="#0284C7"
                      label="Habitation Module"
                      status="NORMAL"
                      isSelected={selectedEquipmentId === 'HVAC-01'}
                      onClick={() => setSelectedEquipmentId('HVAC-01')}
                    />
                    <Station3DModule
                      position={[0, 0, 0]}
                      color="#D97706"
                      label="Power House G1-G4"
                      status="WARNING"
                      isSelected={selectedEquipmentId === 'GEN-01' || selectedEquipmentId === 'GEN-02'}
                      onClick={() => setSelectedEquipmentId('GEN-01')}
                    />
                    <Station3DModule
                      position={[3, 0, 0]}
                      color="#DC2626"
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
                      color="#0284C7"
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
              <div className="absolute bottom-3 left-3 bg-white/90 px-3 py-1.5 rounded border border-slate-200 text-[11px] font-mono text-slate-700 shadow-xs pointer-events-none">
                Mouse Drag: Rotate | Scroll: Zoom | Click module to inspect
              </div>
            </div>
          ) : (
            /* 2D Schematic View Fallback */
            <div className="w-full h-full bg-slate-50 p-4 rounded overflow-auto border border-slate-200 font-mono">
              <div className="text-xs font-bold text-teal-700 mb-4 uppercase tracking-wider flex items-center gap-2">
                <Layers className="w-4 h-4" /> 2D Polar Station Architectural Layout
              </div>

              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {equipment.map((eq) => (
                  <button
                    key={eq.id}
                    onClick={() => setSelectedEquipmentId(eq.id)}
                    className={`p-4 rounded border text-left transition-all ${
                      selectedEquipmentId === eq.id
                        ? 'bg-white border-teal-600 shadow-sm ring-1 ring-teal-600'
                        : 'bg-white border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-[#183153]">{eq.id}</span>
                      <Badge status={eq.status} />
                    </div>
                    <h4 className="text-xs text-teal-800 font-semibold mb-1 truncate">{eq.name}</h4>
                    <p className="text-[10px] text-slate-500">{eq.location}</p>
                    <div className="mt-3 flex items-center justify-between text-[11px] border-t border-slate-100 pt-2">
                      <span className="text-slate-500">Health:</span>
                      <span className="font-bold text-emerald-700">{eq.health}%</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column (1 col): Selected Subsystem Equipment Details Panel */}
        <div className="polar-card p-5 flex flex-col justify-between space-y-4 font-mono">
          <div>
            <div className="flex items-center justify-between border-b border-slate-200 pb-3 mb-4">
              <div>
                <span className="text-[10px] font-mono text-teal-700 uppercase tracking-wider block font-semibold">
                  Equipment Telemetry Panel
                </span>
                <h3 className="text-base font-bold font-mono text-[#183153]">{selectedEquipment.id}</h3>
              </div>
              <Badge status={selectedEquipment.status} size="md" />
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-mono text-slate-500 block mb-0.5">Component Title</label>
                <p className="text-xs font-bold text-teal-800 font-mono bg-slate-50 p-2.5 rounded border border-slate-200">
                  {selectedEquipment.name}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
                  <span className="text-slate-500 block text-[10px]">Category</span>
                  <span className="text-slate-800 font-semibold">{selectedEquipment.category}</span>
                </div>
                <div className="bg-slate-50 p-2.5 rounded border border-slate-200">
                  <span className="text-slate-500 block text-[10px]">Health Score</span>
                  <span className={`font-bold ${selectedEquipment.health > 80 ? 'text-emerald-700' : 'text-amber-600'}`}>
                    {selectedEquipment.health}%
                  </span>
                </div>
              </div>

              <div>
                <label className="text-xs font-mono text-slate-500 block mb-1">Live Sensor Telemetry</label>
                <div className="bg-white p-3 rounded border border-slate-200 font-mono text-xs space-y-2">
                  {Object.entries(selectedEquipment.specs).map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b border-slate-100 pb-1 text-xs">
                      <span className="text-slate-500">{k}:</span>
                      <span className="text-teal-800 font-semibold">{v}</span>
                    </div>
                  ))}
                  <div className="flex justify-between text-xs pt-1">
                    <span className="text-slate-500">Ambient Temp:</span>
                    <span className="text-teal-700 font-semibold">{telemetry.temperature}°C</span>
                  </div>
                </div>
              </div>

              <div className="bg-slate-50 p-3 rounded border border-slate-200 text-xs font-mono space-y-1">
                <div className="flex justify-between">
                  <span className="text-slate-500">Last Service:</span>
                  <span className="text-slate-700">{selectedEquipment.lastMaintenance}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Next Service Due:</span>
                  <span className="text-amber-700 font-semibold">{selectedEquipment.nextMaintenance}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="text-[10px] text-slate-500 font-mono border-t border-slate-200 pt-3 flex items-center justify-between">
            <span>Subsystem ID: {selectedEquipment.subsystemId}</span>
            <span className="text-teal-700 font-semibold">NCPOR Telemetry Sync</span>
          </div>
        </div>
      </div>
    </div>
  );
};
