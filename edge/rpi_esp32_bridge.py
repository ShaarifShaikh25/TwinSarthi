
class RPiESP32Bridge:
    def __init__(self):
        self.connected = True
    def read_sensor_data(self):
        return {"temperature": 22.5, "vibration": 0.05}
