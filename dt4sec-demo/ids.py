import os, json, requests
from datetime import datetime, timezone
import numpy as np
from sklearn.ensemble import IsolationForest
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
TOPIC_SENSOR = "cps/tank/sensors"
TOPIC_ALERTS = "cps/alerts"
TWIN_API = os.getenv("TWIN_API", "http://localhost:10000")
WINDOW = 200

data = []
model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)

def on_connect(client, userdata, flags, reason_code, properties=None):
    client.subscribe(TOPIC_SENSOR)

def maybe_train():
    if len(data) >= 100 and len(data) % 25 == 0:
        X = np.array(data[-WINDOW:])
        model.fit(X)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
        vec = [payload.get("level", 0.0), payload.get("inflow", 0.0), payload.get("outflow", 0.0)]
        data.append(vec)
        if len(data) > WINDOW: del data[0]
        if len(data) >= 100:
            pred = model.predict([vec])[0]
            if pred == -1:
                alert = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "alert": "Anomalous tank behavior detected",
                    "score": float(model.score_samples([vec])[0])
                }
                try:
                    requests.post(f"{TWIN_API}/api/alerts", json=alert, timeout=2)
                except Exception:
                    pass
                client.publish(TOPIC_ALERTS, json.dumps(alert))
        maybe_train()
    except Exception as e:
        print("IDS error:", e, flush=True)

def main():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()
