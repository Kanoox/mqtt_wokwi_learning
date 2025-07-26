# === main.py ===
import sqlite3
import json
from datetime import datetime
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
import os

# === Chargement des variables d'environnement ===
load_dotenv()
MQTT_BROKER_IP = os.getenv("MQTT_BROKER_IP")
MQTT_PORT = int(os.getenv("MQTT_PORT"))

# === Connexion base SQLite ===
conn = sqlite3.connect("capteur_multi.db", check_same_thread=False)
cur = conn.cursor()

# === Création des tables si elles n'existent pas ===
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

# === Callback lors de la connexion au broker ===
def on_connect(client, userdata, flags, rc, properties=None):
    print("✅ Connecté au broker MQTT")
    client.subscribe("wokwi/sensor/#")
    print("📡 Abonnement au topic : wokwi/sensor/#")

# === Callback à la réception d’un message MQTT ===
def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())

        sensor_id = payload["sensor_id"]
        sensor_type = payload["type"]
        value = float(payload["value"])
        lat = float(payload["latitude"])
        lon = float(payload["longitude"])
        timestamp = datetime.now().isoformat()

        # Enregistrer ou mettre à jour le capteur
        cur.execute("""
            INSERT INTO sensors (id, type, latitude, longitude)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                latitude=excluded.latitude,
                longitude=excluded.longitude
        """, (sensor_id, sensor_type, lat, lon))

        # Insérer la mesure
        cur.execute("""
            INSERT INTO measurements (sensor_id, timestamp, value)
            VALUES (?, ?, ?)
        """, (sensor_id, timestamp, value))

        conn.commit()
        print(f"[{timestamp}] ✅ {sensor_id} ({sensor_type}) → {value}")

    except Exception as e:
        print("❌ Erreur traitement MQTT :", e)

# === Initialisation client MQTT ===
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER_IP, MQTT_PORT, keepalive=60)

# === Boucle infinie ===
client.loop_forever()