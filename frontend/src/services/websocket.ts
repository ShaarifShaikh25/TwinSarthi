import { Telemetry, ConnectionState } from '../types';

type TelemetryCallback = (data: Telemetry) => void;
type ConnectionStateCallback = (state: ConnectionState) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private telemetrySubscribers: Set<TelemetryCallback> = new Set();
  private stateSubscribers: Set<ConnectionStateCallback> = new Set();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private mockIntervalTimer: ReturnType<typeof setInterval> | null = null;

  private state: ConnectionState = {
    isConnected: false,
    mode: 'DEMO',
    lastPayloadTime: null,
    error: null,
  };

  constructor() {
    const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
    const wsProto = apiBase.startsWith('https') ? 'wss' : 'ws';
    const host = apiBase.replace(/^https?:\/\//, '');
    this.url = `${wsProto}://${host}/ws`;
  }

  public connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return;
    }

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        this.stopMockFallback();
        this.updateState({
          isConnected: true,
          mode: 'LIVE',
          lastPayloadTime: new Date().toISOString(),
          error: null,
        });
      };

      this.ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          // Backend sends: { timestamp, temperature, energy, fuel, priority, alerts }
          const telemetry: Telemetry = {
            timestamp: payload.timestamp || new Date().toISOString(),
            temperature: typeof payload.temperature === 'number' ? payload.temperature : -28.5,
            energy: typeof payload.energy === 'number' ? payload.energy : 88.0,
            fuel: typeof payload.fuel === 'number' ? payload.fuel : 92.5,
            priority: payload.priority || 'Normal',
            alerts: Array.isArray(payload.alerts) ? payload.alerts : [],
            windSpeed: 38.5,
            humidity: 62.0,
            solarKw: 42.5,
            generatorKw: 110.0,
            batteryPct: 86.0,
            hvacPowerKw: 45.0,
          };

          this.updateState({
            isConnected: true,
            mode: 'LIVE',
            lastPayloadTime: telemetry.timestamp,
            error: null,
          });

          this.notifyTelemetrySubscribers(telemetry);
        } catch (e) {
          console.error('Error parsing WS message payload:', e);
        }
      };

      this.ws.onerror = () => {
        this.handleConnectionFailure('WebSocket Connection Error');
      };

      this.ws.onclose = () => {
        this.handleConnectionFailure('WebSocket Connection Closed');
      };
    } catch (err: any) {
      this.handleConnectionFailure(`Failed to initialize WebSocket: ${err.message}`);
    }
  }

  private handleConnectionFailure(reason: string) {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const timeout = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
      this.reconnectTimer = setTimeout(() => this.connect(), timeout);
    }

    // Switch to DEMO mode & start mock fallback stream
    this.updateState({
      isConnected: false,
      mode: 'DEMO',
      lastPayloadTime: this.state.lastPayloadTime,
      error: `${reason} (Active Fallback: DEMO Mode)`,
    });

    this.startMockFallback();
  }

  private startMockFallback() {
    if (this.mockIntervalTimer) return;

    let baseTemp = -29.4;
    let baseEnergy = 89.2;
    let baseFuel = 94.0;

    this.mockIntervalTimer = setInterval(() => {
      baseTemp += (Math.random() - 0.48) * 0.8;
      baseEnergy += (Math.random() - 0.52) * 0.4;
      baseFuel -= Math.random() * 0.05;

      if (baseTemp < -45) baseTemp = -45;
      if (baseTemp > -12) baseTemp = -12;
      if (baseEnergy < 40) baseEnergy = 40;
      if (baseEnergy > 100) baseEnergy = 100;
      if (baseFuel < 10) baseFuel = 10;

      const priority = baseFuel < 20 ? 'Critical' : baseTemp < -35 ? 'High' : 'Normal';
      const alerts: string[] = [];
      if (baseFuel < 20) alerts.push('Low Fuel Storage');
      if (baseTemp < -35) alerts.push('Extreme Antarctic Blizzard Warning');

      const mockTelemetry: Telemetry = {
        timestamp: new Date().toISOString(),
        temperature: parseFloat(baseTemp.toFixed(2)),
        energy: parseFloat(baseEnergy.toFixed(2)),
        fuel: parseFloat(baseFuel.toFixed(2)),
        priority,
        alerts,
        windSpeed: parseFloat((35 + Math.random() * 15).toFixed(1)),
        humidity: 64,
        solarKw: parseFloat((30 + Math.random() * 20).toFixed(1)),
        generatorKw: 115.0,
        batteryPct: parseFloat((80 + Math.random() * 15).toFixed(1)),
        hvacPowerKw: 48.0,
      };

      this.updateState({
        ...this.state,
        lastPayloadTime: mockTelemetry.timestamp,
      });

      this.notifyTelemetrySubscribers(mockTelemetry);
    }, 2500);
  }

  private stopMockFallback() {
    if (this.mockIntervalTimer) {
      clearInterval(this.mockIntervalTimer);
      this.mockIntervalTimer = null;
    }
  }

  public subscribeTelemetry(callback: TelemetryCallback): () => void {
    this.telemetrySubscribers.add(callback);
    return () => this.telemetrySubscribers.delete(callback);
  }

  public subscribeState(callback: ConnectionStateCallback): () => void {
    this.stateSubscribers.add(callback);
    callback(this.state);
    return () => this.stateSubscribers.delete(callback);
  }

  private notifyTelemetrySubscribers(data: Telemetry) {
    this.telemetrySubscribers.forEach((cb) => cb(data));
  }

  private updateState(newState: ConnectionState) {
    this.state = newState;
    this.stateSubscribers.forEach((cb) => cb(this.state));
  }

  public disconnect() {
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.stopMockFallback();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const wsService = new WebSocketService();
