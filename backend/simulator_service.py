import time
import random
import threading
from datetime import datetime
from ai_logic import process_data

class Simulator:
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.callbacks = []
        
        # Base values
        self.temperature = -25.0
        self.energy = 100.0
        self.fuel = 100.0

    def add_callback(self, callback):
        self.callbacks.append(callback)

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            return True
        return False

    def stop(self):
        self.is_running = False

    def generate_sensor_data(self):
        # Introduce occasional anomalies (~10%)
        is_anomaly = random.random() < 0.10
        
        if is_anomaly:
            # Extreme variation
            self.temperature += random.uniform(-15.0, -5.0)
            self.energy -= random.uniform(5.0, 15.0)
            self.fuel -= random.uniform(10.0, 20.0)
        else:
            # Normal realistic variation
            self.temperature += random.uniform(-2.0, 2.0)
            self.energy -= random.uniform(0.1, 1.0)
            self.fuel -= random.uniform(0.5, 2.0)
            
            # Simple bounds and slow recovery
            if self.temperature < -80: self.temperature = -80
            if self.temperature > 0: self.temperature = 0
            
        # Ensure values stay in percentage bounds
        self.energy = max(0, min(100, self.energy))
        self.fuel = max(0, min(100, self.fuel))

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "temperature": round(self.temperature, 2),
            "energy": round(self.energy, 2),
            "fuel": round(self.fuel, 2)
        }

    def _run_loop(self):
        while self.is_running:
            raw_data = self.generate_sensor_data()
            processed_data = process_data(raw_data)
            
            for callback in self.callbacks:
                try:
                    callback(processed_data)
                except Exception as e:
                    print(f"Error in simulator callback: {e}")
            
            time.sleep(2)

simulator_instance = Simulator()
