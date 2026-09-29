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
  type?: 'habitation' | 'power' | 'lab' | 'fuel' | 'water' | 'comms';
}> = ({ position, color, label, status, isSelected, onClick, type = 'habitation' }) => {
  const [hovered, setHovered] = useState(false);
  
  return (
    <group 
      position={position} 
      onClick={onClick}
      onPointerOver={(e) => { e.stopPropagation(); setHovered(true); }}
      onPointerOut={(e) => { e.stopPropagation(); setHovered(false); }}
    >
      {/* Module Base Pad (Concrete-like) */}
      <mesh position={[0, -0.62, 0]} receiveShadow>
        <boxGeometry args={[3.2, 0.05, 2.6]} />
        <meshStandardMaterial color="#94A3B8" roughness={0.9} />
      </mesh>

      {/* HABITATION */}
      {type === 'habitation' && (
        <group>
          {/* Main block */}
          <mesh castShadow receiveShadow position={[0, 0.1, 0]}>
            <boxGeometry args={[2.6, 1.4, 1.6]} />
            <meshStandardMaterial color="#1E40AF" roughness={0.4} />
          </mesh>
          {/* Roof overhang */}
          <mesh castShadow receiveShadow position={[0, 0.85, 0]}>
            <boxGeometry args={[2.7, 0.1, 1.7]} />
            <meshStandardMaterial color="#CBD5E1" roughness={0.5} />
          </mesh>
          {/* Roof HVAC units */}
          <mesh castShadow receiveShadow position={[-0.8, 0.95, 0]}>
            <boxGeometry args={[0.4, 0.2, 0.4]} />
            <meshStandardMaterial color="#64748B" roughness={0.7} />
          </mesh>
          <mesh castShadow receiveShadow position={[0.8, 0.95, 0.3]}>
            <boxGeometry args={[0.3, 0.2, 0.3]} />
            <meshStandardMaterial color="#64748B" roughness={0.7} />
          </mesh>
          {/* Side extension/airlock */}
          <mesh castShadow receiveShadow position={[0, -0.2, 0.9]}>
            <boxGeometry args={[0.8, 0.8, 0.4]} />
            <meshStandardMaterial color="#475569" roughness={0.5} />
          </mesh>
        </group>
      )}

      {/* LAB */}
      {type === 'lab' && (
        <group>
          <mesh castShadow receiveShadow position={[0, 0, 0]}>
            <boxGeometry args={[2.4, 1.2, 1.8]} />
            <meshStandardMaterial color="#0F172A" roughness={0.3} />
          </mesh>
          {/* Roof overhang */}
          <mesh castShadow receiveShadow position={[0, 0.65, 0]}>
            <boxGeometry args={[2.5, 0.1, 1.9]} />
            <meshStandardMaterial color="#94A3B8" roughness={0.4} />
          </mesh>
          {/* Skylight / observation deck */}
          <mesh castShadow receiveShadow position={[0, 0.8, 0]}>
            <boxGeometry args={[1.2, 0.2, 0.8]} />
            <meshStandardMaterial color="#38BDF8" roughness={0.1} metalness={0.8} />
          </mesh>
          {/* Antenna */}
          <mesh castShadow receiveShadow position={[0.8, 0.9, -0.6]}>
            <cylinderGeometry args={[0.02, 0.02, 0.6]} />
            <meshStandardMaterial color="#E2E8F0" />
          </mesh>
        </group>
      )}

      {/* POWER */}
      {type === 'power' && (
        <group position={[0, -0.1, 0]}>
          {/* Main Generator Housing */}
          <mesh castShadow receiveShadow position={[0, 0.3, 0]}>
            <boxGeometry args={[2.2, 1.0, 1.8]} />
            <meshStandardMaterial color="#334155" roughness={0.6} />
          </mesh>
          {/* Exhaust Stacks */}
          <mesh castShadow receiveShadow position={[-0.6, 1.1, -0.4]}>
            <cylinderGeometry args={[0.15, 0.15, 0.8]} />
            <meshStandardMaterial color="#64748B" />
          </mesh>
          <mesh castShadow receiveShadow position={[0.6, 1.1, -0.4]}>
            <cylinderGeometry args={[0.15, 0.15, 0.8]} />
            <meshStandardMaterial color="#64748B" />
          </mesh>
          {/* Side Vents */}
          <mesh castShadow receiveShadow position={[0, 0.3, 0.95]}>
            <boxGeometry args={[1.4, 0.5, 0.1]} />
            <meshStandardMaterial color="#1E293B" />
          </mesh>
        </group>
      )}

      {/* FUEL */}
      {type === 'fuel' && (
        <group position={[0, 0.1, 0]}>
          {/* Tank 1 */}
          <mesh castShadow receiveShadow position={[-0.8, 0.3, 0]}>
            <cylinderGeometry args={[0.6, 0.6, 1.4, 24]} />
            <meshStandardMaterial color="#F8FAFC" roughness={0.3} />
          </mesh>
          <mesh castShadow receiveShadow position={[-0.8, 1.05, 0]}>
            <cylinderGeometry args={[0.62, 0.62, 0.1, 24]} />
            <meshStandardMaterial color="#CBD5E1" />
          </mesh>
          {/* Tank 2 */}
          <mesh castShadow receiveShadow position={[0.8, 0.3, 0]}>
            <cylinderGeometry args={[0.6, 0.6, 1.4, 24]} />
            <meshStandardMaterial color="#F8FAFC" roughness={0.3} />
          </mesh>
          <mesh castShadow receiveShadow position={[0.8, 1.05, 0]}>
            <cylinderGeometry args={[0.62, 0.62, 0.1, 24]} />
            <meshStandardMaterial color="#CBD5E1" />
          </mesh>
          {/* Connecting pipes */}
          <mesh castShadow receiveShadow position={[0, 0.1, 0]} rotation={[0, 0, Math.PI / 2]}>
            <cylinderGeometry args={[0.08, 0.08, 1.6]} />
            <meshStandardMaterial color="#94A3B8" />
          </mesh>
        </group>
      )}

      {/* COMMS */}
      {type === 'comms' && (
        <group>
          {/* Operations base */}
          <mesh castShadow receiveShadow position={[0, -0.2, 0]}>
            <boxGeometry args={[1.8, 0.8, 1.8]} />
            <meshStandardMaterial color="#1E293B" roughness={0.5} />
          </mesh>
          <mesh castShadow receiveShadow position={[0, 0.25, 0]}>
            <boxGeometry args={[1.9, 0.1, 1.9]} />
            <meshStandardMaterial color="#CBD5E1" />
          </mesh>
          {/* Central Mast */}
          <mesh castShadow receiveShadow position={[0, 0.9, 0]}>
            <cylinderGeometry args={[0.2, 0.3, 1.2, 8]} />
            <meshStandardMaterial color="#64748B" />
          </mesh>
          {/* Radome Dome */}
          <mesh castShadow receiveShadow position={[0, 1.9, 0]}>
            <sphereGeometry args={[0.7, 32, 16]} />
            <meshStandardMaterial color="#F1F5F9" roughness={0.4} />
          </mesh>
          {/* Thin top antenna */}
          <mesh castShadow receiveShadow position={[0, 2.8, 0]}>
            <cylinderGeometry args={[0.02, 0.02, 0.6]} />
            <meshStandardMaterial color="#EF4444" />
          </mesh>
        </group>
      )}

      {/* WATER/WASTE */}
      {type === 'water' && (
        <group position={[0, -0.1, 0]}>
          {/* Treatment building */}
          <mesh castShadow receiveShadow position={[0.6, 0.2, 0]}>
            <boxGeometry args={[1.2, 1.0, 1.4]} />
            <meshStandardMaterial color="#475569" roughness={0.5} />
          </mesh>
          <mesh castShadow receiveShadow position={[0.6, 0.75, 0]}>
            <boxGeometry args={[1.3, 0.1, 1.5]} />
            <meshStandardMaterial color="#CBD5E1" />
          </mesh>
          {/* Holding Tank */}
          <mesh castShadow receiveShadow position={[-0.6, 0.1, 0]}>
            <cylinderGeometry args={[0.7, 0.7, 1.2, 24]} />
            <meshStandardMaterial color="#94A3B8" roughness={0.4} />
          </mesh>
        </group>
      )}

      {/* Hover Selection Outline */}
      {isSelected && (
        <mesh position={[0, -0.58, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[1.6, 1.8, 32]} />
          <meshBasicMaterial color="#0D9488" />
        </mesh>
      )}

      {/* Connector Line to Label */}
      <mesh position={[0, 1.5, 0]}>
        <cylinderGeometry args={[0.01, 0.01, 1.8]} />
        <meshBasicMaterial color={isSelected ? '#0D9488' : '#94A3B8'} />
      </mesh>

      {/* Clean Floating Label */}
      <Html position={[0, 3.2, 0]} center distanceFactor={14} zIndexRange={[100, 0]}>
        <div
          className={`flex flex-col items-center cursor-pointer transition-all duration-300 ${
            isSelected ? 'scale-110' : hovered ? 'scale-105' : 'scale-100'
          }`}
        >
          <div className={`px-3 py-1.5 rounded-sm text-xs font-sans tracking-wide whitespace-nowrap shadow-xl backdrop-blur-md border ${
            isSelected
              ? 'bg-[#0F172A]/95 text-white border-[#0D9488] shadow-[#0D9488]/30'
              : 'bg-[#1E293B]/90 text-slate-200 border-slate-600'
          }`}>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${
                status === 'CRITICAL' ? 'bg-[#EF6461]' : status === 'WARNING' ? 'bg-[#F59E0B]' : 'bg-[#10B981]'
              } ${isSelected ? 'animate-pulse' : ''}`} />
              <span className="font-semibold">{label}</span>
            </div>
            {isSelected && <div className="text-[9px] text-[#38BDF8] mt-0.5 text-center uppercase tracking-widest">Selected</div>}
          </div>
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
                <Canvas shadows camera={{ position: [14, 16, 20], fov: 38 }}>
                  <fog attach="fog" args={['#F1F5F9', 25, 55]} />
                  <ambientLight intensity={0.5} />
                  <directionalLight 
                    position={[20, 25, 10]} 
                    intensity={1.8} 
                    castShadow 
                    shadow-mapSize={[2048, 2048]}
                    shadow-camera-far={60}
                    shadow-camera-left={-20}
                    shadow-camera-right={20}
                    shadow-camera-top={20}
                    shadow-camera-bottom={-20}
                    shadow-bias={-0.0001}
                  />
                  <pointLight position={[-15, 15, -15]} intensity={0.3} color="#94A3B8" />

                  {/* Snow Ground Plane */}
                  <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.7, 0]} receiveShadow>
                    <planeGeometry args={[80, 80]} />
                    <meshStandardMaterial color="#F4F7FA" roughness={0.9} metalness={0.05} />
                  </mesh>

                  {/* Central Base Platform / Main Campus Foundation */}
                  <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.68, 0]} receiveShadow>
                    <boxGeometry args={[18, 14, 0.04]} />
                    <meshStandardMaterial color="#E2E8F0" roughness={1} />
                  </mesh>

                  {/* Concrete/Packed Snow Paths */}
                  <group position={[0, -0.65, 0]}>
                    {/* Main central spine */}
                    <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
                      <planeGeometry args={[14, 1.4]} />
                      <meshStandardMaterial color="#CBD5E1" roughness={0.9} />
                    </mesh>
                    {/* Path to Hab/Lab */}
                    <mesh rotation={[-Math.PI / 2, 0, Math.PI / 2]} position={[2.5, 0, -1]} receiveShadow>
                      <planeGeometry args={[8, 1.4]} />
                      <meshStandardMaterial color="#CBD5E1" roughness={0.9} />
                    </mesh>
                    {/* Path to Power/Fuel */}
                    <mesh rotation={[-Math.PI / 2, 0, Math.PI / 2]} position={[-3, 0, -0.5]} receiveShadow>
                      <planeGeometry args={[7, 1.4]} />
                      <meshStandardMaterial color="#CBD5E1" roughness={0.9} />
                    </mesh>
                  </group>

                  {/* 3D Station Buildings - Campus Layout */}
                  <Suspense fallback={null}>
                    {/* Right Zone: Living & Research */}
                    <Station3DModule
                      position={[2.5, 0, 1.5]}
                      color="#1E40AF"
                      label="Main Station (Habitation)"
                      status="NORMAL"
                      type="habitation"
                      isSelected={selectedEquipmentId === 'HVAC-01'}
                      onClick={() => setSelectedEquipmentId('HVAC-01')}
                    />
                    <Station3DModule
                      position={[2.5, 0, -3.5]}
                      color="#0F172A"
                      label="Research & Living"
                      status="CRITICAL"
                      type="lab"
                      isSelected={selectedEquipmentId === 'HVAC-02'}
                      onClick={() => setSelectedEquipmentId('HVAC-02')}
                    />

                    {/* Left Zone: Utilities & Power */}
                    <Station3DModule
                      position={[-3, 0, 2]}
                      color="#334155"
                      label="Power Generation"
                      status="WARNING"
                      type="power"
                      isSelected={selectedEquipmentId === 'GEN-01' || selectedEquipmentId === 'GEN-02'}
                      onClick={() => setSelectedEquipmentId('GEN-01')}
                    />
                    <Station3DModule
                      position={[-3, 0, -2.5]}
                      color="#F8FAFC"
                      label="Fuel Storage"
                      status="NORMAL"
                      type="fuel"
                      isSelected={selectedEquipmentId === 'FUEL-01'}
                      onClick={() => setSelectedEquipmentId('FUEL-01')}
                    />

                    {/* Outer Zones */}
                    <Station3DModule
                      position={[-7, 0, 0]}
                      color="#475569"
                      label="Water & Waste"
                      status="NORMAL"
                      type="water"
                      isSelected={selectedEquipmentId === 'WTR-01'}
                      onClick={() => setSelectedEquipmentId('WTR-01')}
                    />
                    <Station3DModule
                      position={[7, 0, -1]}
                      color="#1E293B"
                      label="Communication"
                      status="NORMAL"
                      type="comms"
                      isSelected={selectedEquipmentId === 'COM-01'}
                      onClick={() => setSelectedEquipmentId('COM-01')}
                    />
                  </Suspense>

                  <OrbitControls 
                    enablePan={true} 
                    enableZoom={true} 
                    maxPolarAngle={Math.PI / 2.2} 
                    minDistance={8} 
                    maxDistance={40} 
                  />
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
