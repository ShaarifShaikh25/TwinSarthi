# ❄️ TwinSarthi (POLAR-TWIN)
### Predictive & Causal Digital Twin for Antarctic Research Stations (Maitri & Bharati)

Developed as part of the **Smart India Hackathon (SIH)** for Antarctic Life-Support and Infrastructure Resilience.

---
## Live Demo Link : https://twin-sarthi.vercel.app/

<img width="748" height="500" alt="image" src="https://github.com/user-attachments/assets/15c32d01-4f40-49e9-a008-e277b47f77b7" />

<img width="1917" height="915" alt="image" src="https://github.com/user-attachments/assets/798a9029-0d79-41f5-a670-05b964ebdbd3" />
<img width="1917" height="902" alt="image" src="https://github.com/user-attachments/assets/49c7d7fe-43d9-4a73-94fe-64b752f875ab" />

---

## 🌍 Overview
**TwinSarthi** transforms physical Antarctic research stations into an **intelligent digital twin replica**, acting as a virtual assistant ("Sarthi") for station operations with real-time insights, predictive analytics, and mission-critical decision support.

- **Maitri Research Station** (70°45′58″S, 11°44′09″E, Schirmacher Oasis)
- **Bharati Research Station** (69°24′29″S, 76°11′14″E, Larsemann Hills)

---

## 🌟 Key Features & Subsystem Twins
- 📊 **Unified Digital Twin Dashboard**: Multi-domain real-time state for environmental, energy, equipment, and logistics subsystems.
- 🌡️ **Environmental Twin**: Temperature, wind velocity, barometric pressure, relative humidity, visibility.
- ⚡ **Energy Microgrid Twin**: Solar PV, wind turbine, diesel generator load, battery state-of-charge, fuel autonomy hours.
- 🚨 **Rule-Based Alert Engine**: Fast, deterministic safety alerts (fuel critical $<20\%$, emergency $<10\%$, blizzard storm winds $>40\text{ m/s}$, polar deep-freeze $<-50^\circ\text{C}$).
- 📦 **Logistics & Inventory Twin**: Fuel reserves, food, and critical spare parts with daily burn rates and supply-window countdowns.
- 🤖 **Human-in-the-Loop Decision Console**: Full recommendation lifecycle (approve, modify, reject) with complete audit trail.
- 🔮 **AI & Risk Interfaces**: Modular hooks for Developer 3 (Cascading Risk Graph, What-If Simulation, Resupply Priority Matrix).
- 📡 **Real-time WebSockets**: Low-latency channel (`/ws/{station_id}`) streaming 6 typed telemetry and digital twin events.
- 🛡️ **Data Source Honesty**: Transparent provenance tracking (`SIMULATED`, `PUBLIC_HISTORICAL`, `PROTOTYPE_SENSOR`).

---

## 🏗️ System Architecture

```
Sensors / Simulators / Microcontrollers
             ↓ (MQTT:1883 or HTTP /ingest)
   FastAPI Production Backend Core
  - JWT Authentication & RBAC (Admin, Controller, Viewer)
  - Telemetry Validation & Source Honesty Enforcement
  - Real-Time Digital Twin Aggregator
  - Centralized Rule-Based Alert Engine
  - AI & Simulation Service Interfaces
             ↓                                   ↓
PostgreSQL 16 / TimescaleDB           WebSocket Channel Manager
  (High-Throughput Hypertable)           (/ws/{station_id})
                                                 ↓
                                      React 18 + Vite Frontend
                                      (Tailwind CSS, Lucide, Recharts)
```

---

## 🧰 Tech Stack

### Frontend
- React 18, TypeScript, Vite
- Tailwind CSS, Lucide React, Recharts
- Context API (`StationContext`), WebSocket Client

### Backend
- FastAPI, Python 3.11+, Uvicorn
- SQLAlchemy 2.0 ORM, Alembic migrations
- PostgreSQL 16 & TimescaleDB
- Eclipse Mosquitto MQTT Broker
- PyJWT Authentication & PBKDF2 Hashing
- Pytest (33/33 comprehensive tests)

---

## 🚀 Quickstart & Setup

### 1. Clone Repository
```bash
git clone https://github.com/ShaarifShaikh25/TwinSarthi.git
cd TwinSarthi
```

### 2. Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive API Docs: `http://localhost:8000/api/docs`
- Health Probe: `http://localhost:8000/health`
- WebSocket: `ws://localhost:8000/ws/maitri`

#### Docker Compose Deployment
```bash
cd backend
cp .env.example .env
docker compose up -d --build
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing Backend Suite
```bash
cd backend
python -m pytest tests/ -v
```
All 33 tests pass covering 12 core areas and end-to-end integration flow.

---

## 📜 License
Developed for educational, research, and Smart India Hackathon purposes.
