import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from simulator_service import simulator_instance

# Global reference to the asyncio event loop
loop = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global loop
    loop = asyncio.get_running_loop()
    yield
    simulator_instance.stop()

app = FastAPI(title="Antarctic Station Digital Twin", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

def broadcast_data(data: dict):
    """Callback function called by the simulator background thread."""
    if loop is not None and loop.is_running():
        asyncio.run_coroutine_threadsafe(manager.broadcast(data), loop)

# Register the callback to push data to WebSocket clients
simulator_instance.add_callback(broadcast_data)

@app.post("/simulate")
async def start_simulation():
    """Start the background simulation engine."""
    started = simulator_instance.start()
    if started:
        return {"status": "Simulation started successfully"}
    return {"status": "Simulation is already running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time frontend updates."""
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from the frontend, but we need to keep connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
