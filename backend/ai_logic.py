def process_data(data: dict) -> dict:
    """
    Apply AI logic and alerts.
    """
    priority = "Normal"
    alerts = []

    temperature = data.get("temperature", 0)
    fuel = data.get("fuel", 100)

    # AI Logic for Priority
    if fuel < 20:
        priority = "Critical"
    elif temperature < -30:
        priority = "High"

    # Alert System
    if fuel < 20:
        alerts.append("Low Fuel")
    if temperature < -40:
        alerts.append("Extreme Cold")

    data["priority"] = priority
    data["alerts"] = alerts
    
    return data
