
from simulator.digital_twin_what_if import WhatIfSimulator
from ai.optimization_engine import OptimizationEngine
from edge.mqtt_sim import MQTTClientSimulator
from edge.rpi_esp32_bridge import RPiESP32Bridge
from backend.fastapi_app import app
from fastapi.testclient import TestClient

def test_what_if_simulator():
    sim = WhatIfSimulator()
    res = sim.run_simulation({"p": 1})
    assert res["status"] == "success"

def test_optimization_engine():
    eng = OptimizationEngine()
    res = eng.optimize_maintenance_schedule({})
    assert res["cost_savings"] == 1500

def test_mqtt_sim():
    mqtt = MQTTClientSimulator()
    assert mqtt.connect()
    assert mqtt.publish("test", "data")

def test_rpi_esp32_bridge():
    bridge = RPiESP32Bridge()
    data = bridge.read_sensor_data()
    assert "temperature" in data

def test_fastapi_backend():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "POLAR-TWIN Backend Running"}
