import sqlite3
import json
from datetime import datetime
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os

load_dotenv()  # Charge les variables du fichier .env

## Données MQTT ## 
MQTT_BROKER_IP = os.getenv("MQTT_BROKER_IP")
MQTT_PORT = int(os.getenv("MQTT_PORT"))

conn = sqlite3.connect("capteur_multi.db", check_same_thread=False)
cur = conn.cursor()

# Créer les tables si elles n'existent pas
cur.execute("""
CREATE TABLE IF NOT EXISTS sensors (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sensor_id TEXT,
    timestamp TEXT NOT NULL,
    value REAL NOT NULL,
    FOREIGN KEY(sensor_id) REFERENCES sensors(id)
)
""")

conn.commit()

def on_connect(client, userdata, flags, rc, properties=None):
    print("Connecté MQTT")
    client.subscribe("wokwi/sensor/#")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        sensor_id = payload["sensor_id"]
        sensor_type = payload["type"]
        value = payload["value"]
        lat = payload["latitude"]
        lon = payload["longitude"]
        timestamp = datetime.now().isoformat()

        # Insérer capteur s’il n'existe pas
        cur.execute("""
        INSERT OR IGNORE INTO sensors (id, type, latitude, longitude)
        VALUES (?, ?, ?, ?)""", (sensor_id, sensor_type, lat, lon))

        # Insérer mesure
        cur.execute("""
        INSERT INTO measurements (sensor_id, timestamp, value)
        VALUES (?, ?, ?)""", (sensor_id, timestamp, value))

        cur.execute("""
        INSERT INTO sensors (id, type, latitude, longitude)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET latitude=excluded.latitude, longitude=excluded.longitude
        """, (sensor_id, sensor_type, lat, lon))

        conn.commit()
        print(f"[{timestamp}] {sensor_id} → {value}")

    except Exception as e:
        print("Erreur MQTT :", e)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER_IP, MQTT_PORT, 60)
client.loop_forever()
