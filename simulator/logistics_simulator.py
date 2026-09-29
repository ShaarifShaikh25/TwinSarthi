"""
Logistics Simulator
Simulates basic inventory consumption (food, medicine, spare parts).

IMPORTANT: All data is SIMULATION / DEMO DATA.
PROTOTYPE SIMULATION PARAMETERS
"""
from typing import Dict, Any

class LogisticsSimulator:
    def __init__(
        self,
        food_initial: float = 1000.0, food_daily: float = 40.0,
        medicine_initial: float = 500.0, medicine_daily: float = 5.0,
        spares_initial: float = 200.0, spares_daily: float = 2.0
    ):
        self.inventory = {
            "food": {"quantity": food_initial, "daily_consumption": food_daily},
            "medicine": {"quantity": medicine_initial, "daily_consumption": medicine_daily},
            "spare_parts": {"quantity": spares_initial, "daily_consumption": spares_daily}
        }
        
    def calculate_logistics_state(self, interval_minutes: float) -> Dict[str, Any]:
        """
        Updates inventory levels based on standard daily consumption rates.
        """
        state = {}
        interval_days = interval_minutes / (24.0 * 60.0)
        
        for item, data in self.inventory.items():
            consumed = data["daily_consumption"] * interval_days
            self.inventory[item]["quantity"] = max(0.0, data["quantity"] - consumed)
            
            qty = self.inventory[item]["quantity"]
            daily = data["daily_consumption"]
            days_remaining = qty / daily if daily > 0 else 0.0
            
            state[f"{item}_quantity"] = round(float(qty), 2)
            state[f"{item}_daily_consumption"] = round(float(daily), 2)
            state[f"{item}_days_remaining"] = round(float(days_remaining), 2)
            
        return state
