# === dashboard.py ===
import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import pydeck as pdk
import paho.mqtt.publish as publish
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

MQTT_BROKER = "51.38.185.58"
MQTT_TOPIC = "arrosage/commande"

st.set_page_config(page_title="Dashboard Multi-Capteurs", layout="wide")
st_autorefresh(interval=10_000, key="refresh")

# === Chargement des variables d'environnement ===
load_dotenv()
MQTT_BROKER_IP = os.getenv("MQTT_BROKER_IP")

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

# --- Filtres latéraux ---
st.sidebar.title("🧭 Filtres")

# Type de capteur
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

# Capteurs filtrés par type
filtered_sensors = sensors_df[sensors_df["type"].isin(selected_types)]

# Multiselect dynamique : uniquement les capteurs du type sélectionné
selected_sensor_ids = st.sidebar.multiselect(
    "Capteurs à afficher",
    options=filtered_sensors["id"].tolist(),
    default=filtered_sensors["id"].tolist(),
    key="sensor_select"
)

# Données filtrées pour la carte et les graphiques
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

    st.subheader("📍 Coordonnées des capteurs sélectionnés")
    if selected_sensor_ids:
        display_sensors = filtered_sensors[filtered_sensors["id"].isin(selected_sensor_ids)]
        st.dataframe(display_sensors[["id", "type", "latitude", "longitude"]])
    else:
        st.info("Aucun capteur sélectionné.")

    if len(selected_sensor_ids) > 0:
        sensor_id_center = selected_sensor_ids[0]
        center_sensor = map_data[map_data["id"] == str(sensor_id_center)].iloc[0]
        center_lat = center_sensor["latitude"]
        center_lon = center_sensor["longitude"]
    else:
        center_lat = map_data["latitude"].mean()
        center_lon = map_data["longitude"].mean()

    view_state = pdk.ViewState(
        latitude=center_lat,
        longitude=center_lon,
        zoom=14,
        pitch=0,
        bearing=0
    )

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip=tooltip,
        map_style=None
    ))

    # === Commande des arroseurs ===
    st.sidebar.markdown("## 💧 Commande des arroseurs")

    humidity_sensors = filtered_sensors[filtered_sensors["type"] == "humidity"]

    if humidity_sensors.empty:
        st.sidebar.info("Aucun capteur d'humidité disponible pour le contrôle.")
    else:
        threshold = st.sidebar.slider("Seuil automatique d'humidité (%)", 0, 100, 30)
        st.sidebar.markdown("Arrosoir automatique s'active si dernière valeur d'humidité < au seuil automatique")

        for _, row in humidity_sensors.iterrows():
            sensor_id = row["id"]
            lat, lon = row["latitude"], row["longitude"]
            topic = f"arrosage/commande/{sensor_id}"

            st.sidebar.markdown(f"### 🌿 Arroseur `{sensor_id}`")
            st.sidebar.markdown(f"- 📍 `{lat}, {lon}`")

            capteur_data = data_df[data_df["sensor_id"] == sensor_id]
            if not capteur_data.empty:
                latest = capteur_data.sort_values("timestamp", ascending=False).iloc[0]
                st.sidebar.markdown(f"- Dernière humidité : `{latest['value']:.2f} %`")
                if latest['value'] < threshold:
                    publish.single(topic, payload="ON", hostname=MQTT_BROKER_IP)
                    st.sidebar.success(f"✅ Arroseur `{sensor_id}` activé automatiquement")
                else:
                    publish.single(topic, payload="OFF", hostname=MQTT_BROKER_IP)
                    st.sidebar.info(f"🚫 Arroseur `{sensor_id}` désactivé automatiquement")


            col1, col2 = st.sidebar.columns(2)
            if col1.button(f"Activer {sensor_id}", key=f"on_{sensor_id}"):
                publish.single(topic, payload="ON", hostname=MQTT_BROKER_IP)
                st.sidebar.success(f"✅ Arroseur `{sensor_id}` ACTIVÉ")

            if col2.button(f"Désactiver {sensor_id}", key=f"off_{sensor_id}"):
                publish.single(topic, payload="OFF", hostname=MQTT_BROKER_IP)
                st.sidebar.info(f"🚫 Arroseur `{sensor_id}` DÉSACTIVÉ")

# --- Statistiques par type ---
st.subheader("📊 Statistiques par type de capteur")
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
        sensor_data["rolling"] = sensor_data["value"].rolling(window=5).mean()

        sensor_info = map_data[map_data["id"] == str(sensor_id)].iloc[0]
        lat, lon = sensor_info["latitude"], sensor_info["longitude"]

        st.markdown(f"### 📟 Capteur `{sensor_id}` ({sensor_type})")
        st.markdown(f"📍 Position : **{lat}, {lon}**")

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
