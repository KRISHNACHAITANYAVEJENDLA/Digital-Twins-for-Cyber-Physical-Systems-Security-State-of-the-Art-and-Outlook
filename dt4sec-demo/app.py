import os
import asyncio
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import aiosqlite
import json
import paho.mqtt.client as mqtt

MQTT_HOST = os.getenv("MQTT_HOST", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
DB_PATH = os.getenv("DB_PATH", "./twin.db")

TOPIC_SENSOR = "cps/tank/sensors"

app = FastAPI(title="DT4SEC Digital Twin API", version="1.0.0")

# Database
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                level REAL,
                inflow REAL,
                outflow REAL,
                attack_flag INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                alert TEXT NOT NULL,
                score REAL
            )
        """)
        await db.commit()

@app.on_event("startup")
async def startup_event():
    await init_db()
    asyncio.create_task(mqtt_consumer())

# MQTT setup
def on_connect(client, userdata, flags, reason_code, properties=None):
    client.subscribe(TOPIC_SENSOR)

async def mqtt_consumer():
    loop = asyncio.get_event_loop()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect

    def on_message(client, userdata, msg):
        payload = json.loads(msg.payload.decode("utf-8"))
        async def write():
            async with aiosqlite.connect(DB_PATH) as db:
                await db.execute(
                    "INSERT INTO readings (ts, level, inflow, outflow, attack_flag) VALUES (?, ?, ?, ?, ?)",
                    (
                        payload.get("ts"),
                        payload.get("level"),
                        payload.get("inflow"),
                        payload.get("outflow"),
                        int(payload.get("attack_flag", 0)),
                    ),
                )
                await db.commit()
        asyncio.run_coroutine_threadsafe(write(), loop)

    client.on_message = on_message
    client.connect(MQTT_HOST, MQTT_PORT, 60)
    client.loop_start()
    while True:
        await asyncio.sleep(3600)

# API Endpoints
@app.get("/api/readings/latest")
async def latest_reading():
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT ts, level, inflow, outflow, attack_flag FROM readings ORDER BY id DESC LIMIT 1")
        row = await cur.fetchone()
        if not row:
            raise HTTPException(404, "No data yet")
        return {"ts": row[0], "level": row[1], "inflow": row[2], "outflow": row[3], "attack_flag": row[4]}

@app.get("/api/readings/recent")
async def recent(n: int = 200):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT ts, level, inflow, outflow, attack_flag FROM readings ORDER BY id DESC LIMIT ?", (n,))
        rows = await cur.fetchall()
        return [dict(ts=r[0], level=r[1], inflow=r[2], outflow=r[3], attack_flag=r[4]) for r in rows][::-1]

@app.get("/api/alerts")
async def get_alerts(n: int = 50):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT ts, alert, score FROM alerts ORDER BY id DESC LIMIT ?", (n,))
        rows = await cur.fetchall()
        return [dict(ts=r[0], alert=r[1], score=r[2]) for r in rows]

@app.post("/api/alerts")
async def post_alert(alert: dict):
    ts = alert.get("ts") or datetime.now(timezone.utc).isoformat()
    text = alert.get("alert", "Unknown")
    score = float(alert.get("score", 0.0))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO alerts (ts, alert, score) VALUES (?, ?, ?)", (ts, text, score))
        await db.commit()
    return {"status": "ok"}

# Dashboard
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())
