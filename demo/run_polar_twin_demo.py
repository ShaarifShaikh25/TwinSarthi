
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.digital_twin_what_if import WhatIfSimulator
from ai.optimization_engine import OptimizationEngine
from edge.mqtt_sim import MQTTClientSimulator
from edge.rpi_esp32_bridge import RPiESP32Bridge

def main():
    print("Running POLAR-TWIN Full Integration Demo")
    
    bridge = RPiESP32Bridge()
    print("Sensor Data:", bridge.read_sensor_data())
    
    mqtt = MQTTClientSimulator()
    mqtt.connect()
    mqtt.publish("sensors/telemetry", bridge.read_sensor_data())
    
    simulator = WhatIfSimulator()
    print("What-if Sim:", simulator.run_simulation({"temp": 25}))
    
    engine = OptimizationEngine()
    print("Optimization:", engine.optimize_maintenance_schedule({}))
    
    print("Demo completed successfully!")

if __name__ == "__main__":
    main()
