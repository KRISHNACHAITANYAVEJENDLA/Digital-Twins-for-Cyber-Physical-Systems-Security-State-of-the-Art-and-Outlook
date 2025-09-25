import os, time, json, random
from datetime import datetime, timezone
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_SENSOR = "cps/tank/sensors"

level = 50.0
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.connect(MQTT_HOST, MQTT_PORT, 60)
client.loop_start()

while True:
    inflow = 2.0 + random.uniform(-0.5, 0.5)
    outflow = 1.5 + random.uniform(-0.4, 0.4)
    attack = 1 if random.random() < 0.05 else 0
    if attack and random.random() < 0.5:
        inflow *= 3.0
    if attack and random.random() >= 0.5:
        level += random.uniform(10, 20)

    level = max(0.0, level + inflow - outflow + random.uniform(-0.2, 0.2))

    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": round(level, 3),
        "inflow": round(inflow, 3),
        "outflow": round(outflow, 3),
        "attack_flag": attack
    }
    client.publish(TOPIC_SENSOR, json.dumps(payload), qos=0, retain=False)
    time.sleep(0.5)
