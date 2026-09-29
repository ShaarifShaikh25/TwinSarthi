import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  StationId,
  Station,
  Telemetry,
  ConnectionState,
  Equipment,
  InventoryItem,
  Recommendation,
} from '../types';
import {
  STATIONS,
  INITIAL_TELEMETRY,
  INITIAL_EQUIPMENT,
  INITIAL_INVENTORY,
  INITIAL_RECOMMENDATIONS,
} from '../services/mockData';
import { wsService } from '../services/websocket';
import { apiService } from '../services/api';

interface ActionLogEntry {
  id: string;
  recommendationId: string;
  recommendationTitle: string;
  action: 'APPROVED' | 'MODIFIED' | 'REJECTED';
  timestamp: string;
  details?: string;
}

interface StationContextType {
  selectedStationId: StationId;
  setSelectedStationId: (id: StationId) => void;
  stations: Station[];
  currentStation: Station;
  telemetry: Telemetry;
  connectionState: ConnectionState;
  equipment: Equipment[];
  inventory: InventoryItem[];
  recommendations: Recommendation[];
  actionHistory: ActionLogEntry[];
  handleApproveRecommendation: (id: string) => void;
  handleModifyRecommendation: (id: string, modifiedParams: Record<string, any>) => void;
  handleRejectRecommendation: (id: string, reason?: string) => void;
  triggerSimulationEngine: () => Promise<void>;
}

const StationContext = createContext<StationContextType | undefined>(undefined);

export const StationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [selectedStationId, setSelectedStationId] = useState<StationId>('maitri');
  const [telemetry, setTelemetry] = useState<Telemetry>(INITIAL_TELEMETRY.maitri);
  const [connectionState, setConnectionState] = useState<ConnectionState>({
    isConnected: false,
    mode: 'DEMO',
    lastPayloadTime: null,
  });
  const [equipment] = useState<Equipment[]>(INITIAL_EQUIPMENT);
  const [inventory] = useState<InventoryItem[]>(INITIAL_INVENTORY);
  const [recommendations, setRecommendations] = useState<Recommendation[]>(INITIAL_RECOMMENDATIONS);
  const [actionHistory, setActionHistory] = useState<ActionLogEntry[]>([]);

  // Current selected station metadata
  const currentStation = STATIONS.find((s) => s.id === selectedStationId) || STATIONS[0];

  // Subscribe to WebSocket telemetry & state
  useEffect(() => {
    wsService.connect();

    const unsubscribeTelemetry = wsService.subscribeTelemetry((newTelemetry) => {
      setTelemetry((prev) => ({
        ...prev,
        ...newTelemetry,
        stationId: selectedStationId,
      }));
    });

    const unsubscribeState = wsService.subscribeState((newState) => {
      setConnectionState(newState);
    });

    return () => {
      unsubscribeTelemetry();
      unsubscribeState();
    };
  }, [selectedStationId]);

  // When switching station, update base telemetry initial state
  useEffect(() => {
    if (INITIAL_TELEMETRY[selectedStationId]) {
      setTelemetry(INITIAL_TELEMETRY[selectedStationId]);
    }
  }, [selectedStationId]);

  const handleApproveRecommendation = (id: string) => {
    setRecommendations((prev) =>
      prev.map((rec) => (rec.id === id ? { ...rec, status: 'APPROVED' } : rec))
    );
    const target = recommendations.find((r) => r.id === id);
    if (target) {
      setActionHistory((prev) => [
        {
          id: `LOG-${Date.now()}`,
          recommendationId: id,
          recommendationTitle: target.title,
          action: 'APPROVED',
          timestamp: new Date().toISOString(),
          details: `Action [${target.suggestedAction}] confirmed by NCPOR operator.`,
        },
        ...prev,
      ]);
    }
  };

  const handleModifyRecommendation = (id: string, modifiedParams: Record<string, any>) => {
    setRecommendations((prev) =>
      prev.map((rec) =>
        rec.id === id ? { ...rec, status: 'MODIFIED', modifiedParameters: modifiedParams } : rec
      )
    );
    const target = recommendations.find((r) => r.id === id);
    if (target) {
      setActionHistory((prev) => [
        {
          id: `LOG-${Date.now()}`,
          recommendationId: id,
          recommendationTitle: target.title,
          action: 'MODIFIED',
          timestamp: new Date().toISOString(),
          details: `Parameters adjusted: ${JSON.stringify(modifiedParams)}`,
        },
        ...prev,
      ]);
    }
  };

  const handleRejectRecommendation = (id: string, reason?: string) => {
    setRecommendations((prev) =>
      prev.map((rec) => (rec.id === id ? { ...rec, status: 'REJECTED' } : rec))
    );
    const target = recommendations.find((r) => r.id === id);
    if (target) {
      setActionHistory((prev) => [
        {
          id: `LOG-${Date.now()}`,
          recommendationId: id,
          recommendationTitle: target.title,
          action: 'REJECTED',
          timestamp: new Date().toISOString(),
          details: reason || 'Operator rejected recommendation based on field assessment.',
        },
        ...prev,
      ]);
    }
  };

  const triggerSimulationEngine = async () => {
    await apiService.startSimulation();
  };

  return (
    <StationContext.Provider
      value={{
        selectedStationId,
        setSelectedStationId,
        stations: STATIONS,
        currentStation,
        telemetry,
        connectionState,
        equipment,
        inventory,
        recommendations,
        actionHistory,
        handleApproveRecommendation,
        handleModifyRecommendation,
        handleRejectRecommendation,
        triggerSimulationEngine,
      }}
    >
      {children}
    </StationContext.Provider>
  );
};

export const useStation = () => {
  const context = useContext(StationContext);
  if (!context) {
    throw new Error('useStation must be used within a StationProvider');
  }
  return context;
};
