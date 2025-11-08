import streamlit as st
import numpy as np
import rasterio
import matplotlib.pyplot as plt

st.title("Perfil de Elevación (SRTM1)")

# === ENTRADAS ===
lat0 = st.number_input("Latitud inicial", value=8.5, format="%.6f")
lon0 = st.number_input("Longitud inicial", value=-80.0, format="%.6f")
azimuth = st.number_input("Ángulo (grados, 0° = norte, 90° = este)", value=90)

# === PARÁMETROS DEL PERFIL ===
d_start_km = 10
d_end_km = 50
step_m = 500
R = 6371000  # radio medio de la Tierra (m)
dem_path = "/vsicurl/https://agendatic.com/srtm.tif"

# === CÁLCULO DE PUNTOS ===
distances = np.arange(d_start_km * 1000, d_end_km * 1000 + step_m, step_m)
coords = []

for d in distances:
    lat = np.degrees(np.arcsin(
        np.sin(np.radians(lat0)) * np.cos(d / R) +
        np.cos(np.radians(lat0)) * np.sin(d / R) * np.cos(np.radians(azimuth))
    ))
    lon = lon0 + np.degrees(np.arctan2(
        np.sin(np.radians(azimuth)) * np.sin(d / R) * np.cos(np.radians(lat0)),
        np.cos(d / R) - np.sin(np.radians(lat0)) * np.sin(np.radians(lat))
    ))
    coords.append((lon, lat))

# === LECTURA DE ELEVACIONES ===
try:
    with rasterio.open(dem_path) as src:
        elevs = [float(list(src.sample([pt]))[0][0]) for pt in coords]

    # === GRAFICAR PERFIL ===
    d_km = distances / 1000
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(d_km, elevs, color="royalblue", linewidth=1.8)
    ax.set_xlabel("Distancia desde el punto inicial (km)")
    ax.set_ylabel("Elevación (m)")
    ax.set_title(f"Perfil topográfico radial ({azimuth:.0f}°)")
    ax.grid(True, linestyle="--", alpha=0.5)
    st.pyplot(fig)

    st.success(f"Perfil calculado cada {step_m} m entre {d_start_km} km y {d_end_km} km.")

except FileNotFoundError:
    st.error("⚠️ No se encontró el archivo 'data/srtm.tif'. Descárgalo o créalo antes de ejecutar el cálculo.")
