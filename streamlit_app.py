import math
import numpy as np
import requests
import streamlit as st
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

# -------------------- CONFIGURACIÓN BÁSICA --------------------
st.set_page_config(page_title="Perfil de Elevación (Terrarium)", layout="centered")
st.title("📈 Perfil de Elevación (Terrarium / SRTM ≈30 m)")

st.write(
    "Ingresa una coordenada inicial y un ángulo. "
    "La app tomará alturas cada cierto paso entre dos distancias dadas."
)

# -------------------- FUNCIONES AUXILIARES --------------------
def latlon_to_tile(lat, lon, zoom):
    """Convierte lat/lon a coordenadas de tile (x, y) en Web Mercator."""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = (lon + 180.0) / 360.0 * n
    ytile = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
    return xtile, ytile


def get_elevation_terrarium(lat, lon, zoom=12):
    """
    Obtiene la elevación (m) desde los mosaicos Terrarium.
    Zoom 12 ≈ 30–40 m de resolución en el terreno.
    """
    xtile, ytile = latlon_to_tile(lat, lon, zoom)
    x_int, y_int = int(xtile), int(ytile)
    x_frac = xtile - x_int
    y_frac = ytile - y_int

    url = f"https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{zoom}/{x_int}/{y_int}.png"
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return math.nan

    img = Image.open(BytesIO(r.content)).convert("RGB")

    # Posición del pixel dentro del tile (256x256)
    px = int(x_frac * 256)
    py = int(y_frac * 256)

    # Límite por seguridad
    px = max(0, min(255, px))
    py = max(0, min(255, py))

    R, G, B = img.getpixel((px, py))
    elevation = (R * 256 + G + B / 256) - 32768  # fórmula Terrarium
    return elevation


def punto_desde_azimut(lat0, lon0, azimut_deg, distancia_m):
    """
    Calcula un nuevo punto a partir de lat/lon inicial,
    un azimut (grados) y una distancia en metros.
    Fórmulas de geodesia en esfera.
    """
    R = 6371000.0  # radio medio de la Tierra en m
    angulo = math.radians(azimut_deg)

    lat1 = math.radians(lat0)
    lon1 = math.radians(lon0)

    d_R = distancia_m / R

    lat2 = math.asin(
        math.sin(lat1) * math.cos(d_R)
        + math.cos(lat1) * math.sin(d_R) * math.cos(angulo)
    )

    lon2 = lon1 + math.atan2(
        math.sin(angulo) * math.sin(d_R) * math.cos(lat1),
        math.cos(d_R) - math.sin(lat1) * math.sin(lat2),
    )

    return math.degrees(lat2), math.degrees(lon2)


# -------------------- INTERFAZ --------------------
st.subheader("Parámetros de entrada")

col1, col2 = st.columns(2)
with col1:
    lat0 = st.number_input("Latitud inicial (°)", value=8.5, format="%.6f")
    dist_inicio_km = st.number_input("Distancia inicial (km)", value=10.0, min_value=0.0)
with col2:
    lon0 = st.number_input("Longitud inicial (°)", value=-80.0, format="%.6f")
    dist_fin_km = st.number_input("Distancia final (km)", value=50.0, min_value=0.1)

paso_m = st.number_input("Paso entre muestras (m)", value=500, min_value=10)
azimut = st.number_input("Ángulo (grados, 0° = norte, 90° = este)", value=90)

calcular = st.button("Calcular perfil de elevación")

# -------------------- LÓGICA PRINCIPAL --------------------
if calcular:
    if dist_fin_km <= dist_inicio_km:
        st.error("La distancia final debe ser mayor que la inicial.")
    else:
        st.info("Consultando elevaciones desde mosaicos Terrarium…")

        distancias_m = np.arange(dist_inicio_km * 1000, dist_fin_km * 1000 + paso_m, paso_m)
        elevaciones = []

        progress = st.progress(0)
        total = len(distancias_m)

        for i, d in enumerate(distancias_m):
            lat_p, lon_p = punto_desde_azimut(lat0, lon0, azimut, d)
            elev = get_elevation_terrarium(lat_p, lon_p, zoom=12)
            elevaciones.append(elev)

            progress.progress(int((i + 1) / total * 100))

        elevaciones = np.array(elevaciones, dtype=float)
        dist_km = distancias_m / 1000.0

        # -------------------- GRÁFICO --------------------
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.plot(dist_km, elevaciones, linewidth=2)
        ax.set_xlabel("Distancia desde el punto inicial (km)")
        ax.set_ylabel("Altura (m)")
        ax.set_title("Perfil de Elevación (Terrarium)")
        ax.grid(True, linestyle="--", alpha=0.5)

        st.pyplot(fig)

        st.success(f"Perfil calculado cada {paso_m} m entre {dist_inicio_km} y {dist_fin_km} km.")
        st.caption("Fuente de datos: elevation-tiles-prod (Terrarium, basado en SRTM / Copernicus)")

st.pyplot(fig)

st.success(f"Perfil calculado cada {paso_m} m entre {dist_inicio_km} y {dist_fin_km} km.")
st.caption("Fuente de datos: elevation-tiles-prod (Terrarium, basado en SRTM / Copernicus)")

        # --- Cálculo de Delta H excluyendo extremos 10% ---
        valores_validos = [h for h in elevaciones if not np.isnan(h)]
        n = len(valores_validos)

        if n >= 10:
            # Ordenar alturas y recortar 10% por cada extremo
            valores_ordenados = np.sort(valores_validos)
            corte = int(n * 0.10)
            valores_filtrados = valores_ordenados[corte : n - corte]

            # Calcular Delta H
            delta_h = np.max(valores_filtrados) - np.min(valores_filtrados)

            # Mostrar resultados
            st.subheader("Análisis del perfil")
            st.write(f"Alturas analizadas: {len(valores_validos)}")
            st.write(f"Alturas filtradas (80% central): {len(valores_filtrados)}")
            st.write(f"**ΔH = {delta_h:.2f} m**")

            # Mostrar lista de las 60 alturas filtradas
            st.text_area("Alturas filtradas (m)", "\n".join(f"{h:.2f}" for h in valores_filtrados), height=150)
        else:
            st.warning("Muy pocos puntos válidos para calcular ΔH.")

