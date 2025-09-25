import random

def generate_sensor_data(robot_id: str):
    """Simulate robotic arm sensor readings"""
    return {
        "robot": robot_id,
        "temperature": round(random.uniform(20, 80), 2),
        "pressure": round(random.uniform(1, 10), 2),
        "speed": round(random.uniform(100, 500), 2)
    }
