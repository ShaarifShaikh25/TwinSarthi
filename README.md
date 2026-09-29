# TwinSarthi (POLAR-TWIN)

**Predictive & Causal Digital Twin for Antarctic Research Stations (Maitri & Bharati)**

Developed for the Smart India Hackathon (SIH) Antarctic Life-Support and Infrastructure Resilience Problem Statement.

---

## 🌟 Key Highlights & Capabilities
- **Dual Antarctic Stations Support**: Real-time modeling for **Maitri** (Schirmacher Oasis) and **Bharati** (Larsemann Hills).
- **Subsystem Twins**: Environment, Energy Microgrid (Solar, Wind, DG), Equipment Health, and Logistics Stock.
- **FastAPI Backend Core**: RESTful API + real-time WebSocket channel (`/ws/{station_id}`).
- **TimescaleDB / PostgreSQL**: High-throughput time-series telemetry persistence.
- **Data Source Honesty**: Transparent provenance tracking (`SIMULATED`, `PUBLIC_HISTORICAL`, `PROTOTYPE_SENSOR`).
- **Rule-Based Alert Engine**: Fast, deterministic safety alerts (fuel emergency, blizzard winds, polar cold, DG overload).
- **Human-in-the-Loop Decision Console**: Full recommendation lifecycle (approve, modify, reject) with audit tracking.
- **AI & Risk Interfaces**: Modular extension interfaces for Developer 3 (Cascading Risk, What-If Simulation, Resupply Optimization).
- **Docker Ready**: `Dockerfile` + `docker-compose.yml` for backend, postgres/timescaledb, and eclipse-mosquitto MQTT broker.

---

## 🚀 Quickstart

### 1. Local Run
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- API Docs: `http://localhost:8000/api/docs`
- Health: `http://localhost:8000/health`
- WebSocket: `ws://localhost:8000/ws/maitri`

### 2. Docker Compose
```bash
cd backend
cp .env.example .env
docker compose up -d --build
```

---

## 🧪 Testing
```bash
cd backend
python -m pytest tests/ -v
```
All 33/33 tests covering 12 core areas and complete E2E integration pipeline pass.
