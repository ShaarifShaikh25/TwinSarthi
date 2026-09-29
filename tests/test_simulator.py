import pytest
from datetime import datetime
from simulator.scenarios.normal import generate_normal_scenario

def test_correct_number_of_records():
    res = generate_normal_scenario(periods=10)
    assert len(res) == 10

def test_chronological_timestamps():
    res = generate_normal_scenario(periods=5, interval_minutes=60)
    for i in range(1, len(res)):
        t1 = datetime.fromisoformat(res[i-1]['timestamp'])
        t2 = datetime.fromisoformat(res[i]['timestamp'])
        assert t2 > t1
        assert (t2 - t1).total_seconds() == 3600

def test_required_fields_exist():
    res = generate_normal_scenario(periods=1)
    record = res[0]
    required_top = ["timestamp", "station_id", "environment", "energy", "generator", "fuel", "inventory"]
    for req in required_top:
        assert req in record
        
    required_env = ["temperature_c", "wind_speed_mps", "humidity_percent"]
    for req in required_env:
        assert req in record["environment"]

def test_values_within_range():
    res = generate_normal_scenario(periods=100, seed=1)
    for record in res:
        assert -90.0 <= record['environment']['temperature_c'] <= 15.0
        assert 0.0 <= record['environment']['wind_speed_mps'] <= 100.0
        assert 0.0 <= record['environment']['humidity_percent'] <= 100.0

def test_reproducibility():
    res1 = generate_normal_scenario(periods=5, seed=42)
    res2 = generate_normal_scenario(periods=5, seed=42)
    assert res1 == res2

def test_different_timestamps_produce_changing_values():
    res = generate_normal_scenario(periods=10, seed=42)
    temps = [r['environment']['temperature_c'] for r in res]
    assert len(set(temps)) > 1, "Values should drift, not remain identical"

def test_station_ids():
    res_m = generate_normal_scenario(station_id="MAITRI", periods=1)
    res_b = generate_normal_scenario(station_id="BHARATI", periods=1)
    assert res_m[0]['station_id'] == "MAITRI"
    assert res_b[0]['station_id'] == "BHARATI"

def test_energy_values_generated():
    res = generate_normal_scenario(periods=1)
    record = res[0]
    assert 'power_consumption_kw' in record['energy']
    assert 'hvac_load_kw' in record['energy']
    assert 'generator_load_percent' in record['energy']

def test_hvac_increases_when_cold():
    # Force two scenarios with different base temps to compare HVAC
    from simulator.energy_simulator import EnergySimulator
    sim = EnergySimulator()
    warm_state = sim.calculate_energy_state(temperature_c=0.0, wind_speed_mps=5.0)
    cold_state = sim.calculate_energy_state(temperature_c=-20.0, wind_speed_mps=5.0)
    
    assert cold_state['hvac_load_kw'] > warm_state['hvac_load_kw']

def test_generator_load_responds():
    from simulator.energy_simulator import EnergySimulator
    sim = EnergySimulator()
    low_power = sim.calculate_energy_state(temperature_c=0.0, wind_speed_mps=0.0)
    high_power = sim.calculate_energy_state(temperature_c=-40.0, wind_speed_mps=20.0)
    
    assert high_power['generator_load_percent'] > low_power['generator_load_percent']

def test_fuel_decreases_over_time():
    res = generate_normal_scenario(periods=5, interval_minutes=60)
    fuel_levels = [r['fuel']['level_liters'] for r in res]
    for i in range(1, len(fuel_levels)):
        assert fuel_levels[i] < fuel_levels[i-1]

def test_fuel_never_negative():
    from simulator.fuel_simulator import FuelSimulator
    sim = FuelSimulator(initial_level_liters=5.0)
    # Burn 10 liters worth
    state = sim.calculate_fuel_state(generator_load_percent=100.0, interval_minutes=6000)
    assert state['level_liters'] == 0.0

def test_fuel_days_remaining():
    from simulator.fuel_simulator import FuelSimulator
    sim = FuelSimulator(initial_level_liters=1000.0)
    # Mock specific consumption
    state = sim.calculate_fuel_state(generator_load_percent=0.0, interval_minutes=60)
    # If base_lph = 10, lpd = 240. 1000 liters / 240 lpd = 4.16 days remaining
    # After 1 hour, level is 990. 990 / 240 = 4.125
    assert state['days_remaining'] > 0

def test_inventory_decreases():
    res = generate_normal_scenario(periods=5, interval_minutes=60*24) # 1 day jumps
    food_levels = [r['inventory']['food_quantity'] for r in res]
    for i in range(1, len(food_levels)):
        assert food_levels[i] < food_levels[i-1]

def test_inventory_days_remaining():
    res = generate_normal_scenario(periods=2, interval_minutes=60)
    assert res[0]['inventory']['food_days_remaining'] > 0

def test_generator_runtime_increases():
    res = generate_normal_scenario(periods=5, interval_minutes=60)
    runtimes = [r['generator']['runtime_hours'] for r in res]
    for i in range(1, len(runtimes)):
        assert runtimes[i] > runtimes[i-1]
        
if __name__ == '__main__':
    pytest.main(["-v", __file__])
