from simulators import generate_sensor_data

def ingest_data():
    """Collect simulated data from multiple robotic arms"""
    robots = ["RoboticArm_01", "RoboticArm_02"]
    return [generate_sensor_data(r) for r in robots]
