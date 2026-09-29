import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { StationProvider } from './context/StationContext';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { ErrorBoundary } from './components/ui/ErrorBoundary';

import { MissionControl } from './pages/MissionControl';
import { Energy } from './pages/Energy';
import { Infrastructure } from './pages/Infrastructure';
import { Logistics } from './pages/Logistics';
import { RiskCenter } from './pages/RiskCenter';
import { WhatIfSimulator } from './pages/WhatIfSimulator';
import { RefreshCw } from 'lucide-react';

// Lazy load 3D DigitalTwin page for performance
const DigitalTwin = lazy(() => import('./pages/DigitalTwin'));

const LoadingFallback: React.FC = () => (
  <div className="flex items-center justify-center min-h-[400px] text-slate-500 text-xs gap-2">
    <RefreshCw className="w-5 h-5 text-[#0D9488] animate-spin" />
    <span>Loading Station Digital Twin Module...</span>
  </div>
);

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <Router>
        <StationProvider>
          <div className="min-h-screen bg-[#F1F5F9] text-[#1E293B] flex flex-col font-sans">
            {/* Top Mission Command Header */}
            <Header />

            {/* Main Body with Sidebar + Viewport */}
            <div className="flex-1 flex flex-col md:flex-row min-h-[calc(100vh-57px)]">
              <Sidebar />

              <main className="flex-1 overflow-y-auto bg-[#F1F5F9] p-2">
                <ErrorBoundary>
                  <Suspense fallback={<LoadingFallback />}>
                    <Routes>
                      <Route path="/" element={<MissionControl />} />
                      <Route path="/digital-twin" element={<DigitalTwin />} />
                      <Route path="/energy" element={<Energy />} />
                      <Route path="/infrastructure" element={<Infrastructure />} />
                      <Route path="/logistics" element={<Logistics />} />
                      <Route path="/risk-center" element={<RiskCenter />} />
                      <Route path="/what-if" element={<WhatIfSimulator />} />
                      <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                  </Suspense>
                </ErrorBoundary>
              </main>
            </div>
          </div>
        </StationProvider>
      </Router>
    </ErrorBoundary>
  );
};

export default App;
