# === dashboard.py ===
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import pydeck as pdk
import paho.mqtt.publish as publish
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta

MQTT_BROKER = "51.38.185.58"
MQTT_TOPIC = "arrosage/commande"

st.set_page_config(page_title="Dashboard Multi-Capteurs", layout="wide")
st_autorefresh(interval=10_000, key="refresh")

@st.cache_data(ttl=5)
def load_data():
    conn = sqlite3.connect("capteur_multi.db")
    sensors = pd.read_sql_query("SELECT * FROM sensors", conn)
    measurements = pd.read_sql_query("""
        SELECT m.*, s.type
        FROM measurements m
        JOIN sensors s ON m.sensor_id = s.id
        ORDER BY m.timestamp ASC
    """, conn, parse_dates=["timestamp"])
    return sensors, measurements

sensors_df, data_df = load_data()

# 🔁 Garder uniquement les capteurs actifs récemment
RECENT_THRESHOLD_MINUTES = 10
now = datetime.now()
recent_cutoff = now - timedelta(minutes=RECENT_THRESHOLD_MINUTES)
recent_sensor_ids = data_df[data_df["timestamp"] >= recent_cutoff]["sensor_id"].unique()

sensors_df = sensors_df[sensors_df["id"].isin(recent_sensor_ids)]
data_df = data_df[data_df["sensor_id"].isin(recent_sensor_ids)]

# --- Filtres ---
st.sidebar.title("🗭 Filtres & Arrosage")
sensor_types = sensors_df["type"].unique().tolist()
selected_types = st.sidebar.multiselect("Type de capteurs", sensor_types, default=sensor_types)
filtered_sensors = sensors_df[sensors_df["type"].isin(selected_types)]
selected_sensor_ids = st.sidebar.multiselect("Capteurs à afficher", filtered_sensors["id"], default=filtered_sensors["id"])
filtered_data = data_df[data_df["sensor_id"].isin(selected_sensor_ids)]

# --- Arrosage automatique ---
st.sidebar.markdown("## 💧 Contrôle Arrosage")
humidity_data = data_df[data_df["type"] == "humidity"]
auto_threshold = st.sidebar.slider("Seuil d'humidité (%)", 0, 100, 30)
if not humidity_data.empty:
    mean_humidity = humidity_data["value"].mean()
    st.sidebar.write(f"Humidité moyenne : **{mean_humidity:.2f} %**")
    if mean_humidity < auto_threshold:
        publish.single(MQTT_TOPIC, payload="ON", hostname=MQTT_BROKER)
        st.sidebar.success("Arrosage automatique ACTIVÉ")
    else:
        publish.single(MQTT_TOPIC, payload="OFF", hostname=MQTT_BROKER)
        st.sidebar.info("Arrosage automatique DÉSACTIVÉ")
else:
    st.sidebar.warning("Aucune donnée d'humidité")

if st.sidebar.button("Activer manuellement l'arrosage 🌿"):
    publish.single(MQTT_TOPIC, payload="ON", hostname=MQTT_BROKER)
    st.sidebar.success("Arrosage manuel ACTIVÉ")

if st.sidebar.button("Désactiver l'arrosage ❄️"):
    publish.single(MQTT_TOPIC, payload="OFF", hostname=MQTT_BROKER)
    st.sidebar.info("Arrosage manuel DÉSACTIVÉ")

# --- Carte ---
st.subheader("📽️ Carte interactive")
st.markdown(f"🟢 *Affichage limité aux capteurs ayant émis une mesure dans les {RECENT_THRESHOLD_MINUTES} dernières minutes.*")

if filtered_sensors.empty:
    st.warning("Aucun capteur à afficher.")
else:
    map_data = filtered_sensors.copy()
    map_data[["latitude", "longitude"]] = map_data[["latitude", "longitude"]].apply(pd.to_numeric)
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position='[longitude, latitude]',
        get_radius=100,
        get_fill_color='[200, 30, 0, 160]',
        pickable=True
    )
    view_state = pdk.ViewState(
        latitude=map_data["latitude"].mean(),
        longitude=map_data["longitude"].mean(),
        zoom=13
    )
    tooltip = {
        "html": "<b>ID:</b> {id}<br/><b>Type:</b> {type}<br/><b>Lat:</b> {latitude}<br/><b>Lon:</b> {longitude}",
        "style": {"backgroundColor": "black", "color": "white"}
    }
    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=None
    ))

# --- Statistiques ---
st.subheader("📊 Statistiques")
for sensor_type in selected_types:
    ids = sensors_df[sensors_df["type"] == sensor_type]["id"]
    subset = data_df[data_df["sensor_id"].isin(ids)]
    if not subset.empty:
        st.markdown(f"### Type `{sensor_type}`")
        st.write(f"- Moyenne : {subset['value'].mean():.2f}")
        st.write(f"- Min : {subset['value'].min():.2f}")
        st.write(f"- Max : {subset['value'].max():.2f}")

# --- Graphiques ---
st.subheader("📈 Evolution des capteurs")
for sensor_id in selected_sensor_ids:
    sensor_data = filtered_data[filtered_data["sensor_id"] == sensor_id]
    if not sensor_data.empty:
        sensor_data = sensor_data.copy()
        sensor_data["rolling"] = sensor_data["value"].rolling(5).mean()
        st.markdown(f"### Capteur `{sensor_id}`")
        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(sensor_data["timestamp"], sensor_data["value"], label="Valeur")
        ax.plot(sensor_data["timestamp"], sensor_data["rolling"], linestyle="--", label="Moyenne roulante")
        ax.set_xlabel("Temps")
        ax.set_ylabel("Valeur")
        ax.legend()
        st.pyplot(fig)

# --- Données brutes ---
with st.expander("🔍 Données brutes"):
    st.write(f"{len(filtered_data)} mesures affichées.")
    st.dataframe(filtered_data)
