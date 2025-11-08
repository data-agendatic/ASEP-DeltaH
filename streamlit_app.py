import streamlit as st
import requests
import numpy as np
import matplotlib.pyplot as plt
from math import sin, cos, radians

st.set_page_config(page_title="Perfil de Elevación (SRTM1)", layout="centered")
st.title("📈 Perfil de Elevación (SRTM1)")

# --- Entradas ---
lat = st.number_input("Latitud inicial", value=8.5, format="%.6f")
lon = st.number_input("Longitud inicial", value=-80.0, format="%.6f")
azimut = st.number_input("Ángulo (grados, 0° = norte, 90° = este)", value=90)
dist_inicial_km = st.number_input("Distancia inicial (km)", value=10.0)
dist_final_km = st.number_input("Distancia final (km)", value=50.0)
paso_m = st.number_input("Paso (m)", value=500)

# --- Botón de cálculo ---
if st.button("Calcular perfil"):
    st.info("Consultando elevaciones desde el servicio USGS...")

    # Generar distancias (en metros)
    distancias_m = np.arange(dist_inicial_km * 1000, dist_final_km * 1000, paso_m)
    elevaciones = []

    # Recorremos los puntos cada 500 m
    for d in distancias_m:
        dx = d * sin(radians(azimut)) / 111320  # longitud aproximada por metro
        dy = d * cos(radians(azimut)) / 110540  # latitud aproximada por metro
        lat_p = lat + dy
        lon_p = lon + dx

        # Llamada a la API de USGS
        url = f"https://nationalmap.gov/epqs/pqs.php?x={lon_p}&y={lat_p}&units=Meters&output=json"
        try:
            r = requests.get(url, timeout=5)
            alt = r.json()['USGS_Elevation_Point_Query_Service']['Elevation_Query']['Elevation']
            elevaciones.append(alt)
        except Exception as e:
            elevaciones.append(np.nan)

    # --- Gráfico ---
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(distancias_m / 1000, elevaciones, color="forestgreen", linewidth=2)
    ax.set_xlabel("Distancia (km)")
    ax.set_ylabel("Altura (m)")
    ax.set_title("Perfil de Elevación (consultado vía API)")
    ax.grid(True, linestyle="--", alpha=0.6)
    st.pyplot(fig)

    st.success("✅ Perfil generado correctamente.")
