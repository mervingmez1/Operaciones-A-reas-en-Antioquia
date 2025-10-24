import random
import os
import requests
from dotenv import load_dotenv

# --- Configuración global ---
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
USE_REAL_DATA = False  # Cambia a True cuando quieras usar datos reales (requiere API)

# --- Fuente de datos ---
fuente_datos = (
    "Datos meteorológicos obtenidos desde API externa (OpenWeather)"
    if USE_REAL_DATA
    else "Datos meteorológicos simulados (sin conexión a API real)"
)


# ============================================================
# FUNCIONES DE OBTENCIÓN DE CONDICIONES
# ============================================================

def obtener_condiciones_simuladas():
    """Genera condiciones meteorológicas aleatorias (modo offline)."""
    condiciones = {
        "temperatura": round(random.uniform(15, 35), 1),
        "viento": round(random.uniform(0, 25), 1),
        "visibilidad": round(random.uniform(1000, 10000), 0),  # en metros
        "nubosidad": random.choice(["Despejado", "Parcial", "Nublado", "Tormentoso"]),
    }
    return condiciones


def obtener_condiciones_reales(lat, lon):
    """Obtiene datos reales desde la API de OpenWeatherMap."""
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
    )
    respuesta = requests.get(url)
    datos = respuesta.json()

    condiciones = {
        "temperatura": datos["main"]["temp"],
        "viento": round(datos["wind"]["speed"] * 3.6, 1),  # m/s → km/h
        "visibilidad": datos.get("visibility", 0),  # en metros
        "nubosidad": datos["weather"][0]["description"].capitalize(),
    }
    return condiciones


def obtener_condiciones_meteorologicas(aeropuerto):
    """Devuelve las condiciones (reales o simuladas según configuración)."""
    if USE_REAL_DATA:
        return obtener_condiciones_reales(aeropuerto["lat"], aeropuerto["lon"])
    else:
        return obtener_condiciones_simuladas()


# ============================================================
# FUNCIÓN DE EVALUACIÓN DE SEGURIDAD
# ============================================================

def es_condicion_segura(condiciones):
    """
    Evalúa si las condiciones son aptas para vuelo visual (VFR).
    Criterios básicos:
      - Viento <= 25 km/h
      - Visibilidad >= 5000 m
      - Nubosidad: Despejado o Parcial
    """
    viento_ok = condiciones["viento"] <= 25
    vis_ok = condiciones["visibilidad"] >= 5000
    cielo_ok = any(p in condiciones["nubosidad"].lower() for p in ["despejado", "parcial"])

    return viento_ok and vis_ok and cielo_ok
