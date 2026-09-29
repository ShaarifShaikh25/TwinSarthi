import axios from 'axios';
import { SimulationResult } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiService = {
  /**
   * Triggers the backend simulation engine (POST /simulate)
   */
  async startSimulation(): Promise<{ status: string }> {
    try {
      const response = await apiClient.post<{ status: string }>('/simulate');
      return response.data;
    } catch (error: any) {
      console.warn('Backend /simulate failed or unavailable, falling back to local trigger:', error.message);
      return { status: 'Simulation triggered (Demo Mode)' };
    }
  },

  /**
   * Adapter for future scenario simulation endpoint POST /api/simulate-scenario
   */
  async runScenarioSimulation(scenarioId: string, params: Record<string, any>): Promise<SimulationResult | null> {
    try {
      const response = await apiClient.post<SimulationResult>('/api/simulate-scenario', {
        scenarioId,
        params,
      });
      return { ...response.data, isDemo: false };
    } catch {
      // Endpoint not yet implemented on backend -> Return null to trigger fallback mock generator with clear DEMO flag
      return null;
    }
  }
};
