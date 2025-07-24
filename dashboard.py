import streamlit as st
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import pydeck as pdk
from streamlit_autorefresh import st_autorefresh

# --- Configuration Streamlit ---
st.set_page_config(page_title="Dashboard Multi-Capteurs", layout="wide")
st_autorefresh(interval=10_000, key="refresh")

# --- Chargement des données depuis SQLite ---
@st.cache_data(ttl=5)
def load_data():
    conn = sqlite3.connect("capteur_multi.db")
    sensors = pd.read_sql_query("SELECT * FROM sensors", conn)
    measurements = pd.read_sql_query("SELECT * FROM measurements", conn, parse_dates=["timestamp"])
    return sensors, measurements

sensors_df, data_df = load_data()

# --- Filtres latéraux ---
st.sidebar.title("🧭 Filtres")
sensor_types = sensors_df["type"].unique().tolist()
selected_types = st.sidebar.multiselect("Type de capteurs", sensor_types, default=sensor_types)

filtered_sensors = sensors_df[sensors_df["type"].isin(selected_types)]
selected_sensor_ids = st.sidebar.multiselect(
    "Capteurs à afficher",
    options=filtered_sensors["id"],
    default=filtered_sensors["id"]
)

filtered_data = data_df[data_df["sensor_id"].isin(selected_sensor_ids)]

# --- Carte interactive avec info-bulle ---
st.subheader("🗺️ Carte interactive des capteurs")

if filtered_sensors.empty:
    st.warning("Aucun capteur à afficher.")
else:
    map_data = filtered_sensors.copy()
    map_data["id"] = map_data["id"].astype(str)
    map_data["type"] = map_data["type"].astype(str)
    map_data["latitude"] = pd.to_numeric(map_data["latitude"])
    map_data["longitude"] = pd.to_numeric(map_data["longitude"])

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position='[longitude, latitude]',
        get_radius=100,
        get_fill_color='[200, 30, 0, 160]',
        pickable=True,
    )

    tooltip = {
        "html": """
        <b>🆔 ID:</b> {id}<br/>
        <b>📟 Type:</b> {type}<br/>
        <b>📍 Latitude:</b> {latitude}<br/>
        <b>📍 Longitude:</b> {longitude}
        """,
        "style": {"backgroundColor": "black", "color": "white"}
    }

    st.subheader("📍 Coordonnées des capteurs sélectionnés")
    st.dataframe(filtered_sensors[["id", "type", "latitude", "longitude"]])



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

# --- Statistiques par type ---
st.subheader("📊 Statistiques par type de capteur")
for sensor_type in selected_types:
    ids = sensors_df[sensors_df["type"] == sensor_type]["id"]
    subset = data_df[data_df["sensor_id"].isin(ids)]
    if not subset.empty:
        st.markdown(f"### Type : `{sensor_type}`")
        st.write(f"- Moyenne : {subset['value'].mean():.2f}")
        st.write(f"- Min : {subset['value'].min():.2f}")
        st.write(f"- Max : {subset['value'].max():.2f}")
    else:
        st.info(f"Aucune donnée pour les capteurs de type `{sensor_type}`")

# --- Graphiques par capteur ---
st.subheader("📈 Évolution des valeurs")
for sensor_id in selected_sensor_ids:

    sensor_type = sensors_df[sensors_df["id"] == sensor_id]["type"].values[0]
    sensor_data = filtered_data[filtered_data["sensor_id"] == sensor_id]
    if not sensor_data.empty:
        sensor_data["rolling"] = sensor_data["value"].rolling(window=5).mean()
        
        # --- Affiche position du capteur sélectionné ---
        sensor_info = map_data[map_data["id"] == str(selected_sensor_ids[0])].iloc[0]

        lat, lon = sensor_info["latitude"], sensor_info["longitude"]

        st.markdown(f"### 📟 Capteur `{sensor_id}` ({sensor_type})")
        st.markdown(f"📍 Position : **{lat}, {lon}**")

        fig, ax = plt.subplots(figsize=(10, 3))
        ax.plot(sensor_data["timestamp"], sensor_data["value"], label="Valeur")
        ax.plot(sensor_data["timestamp"], sensor_data["rolling"], linestyle="--", label="Moyenne roulante (5)")
        ax.set_xlabel("Temps")
        ax.set_ylabel("Valeur")
        ax.legend()
        plt.xticks(rotation=45)
        st.pyplot(fig)
    else:
        st.info(f"Aucune donnée pour le capteur `{sensor_id}`")

# --- Données brutes ---
with st.expander("🔍 Voir les données brutes"):
    st.write(f"{len(filtered_data)} mesures affichées.")
    st.dataframe(filtered_data)
