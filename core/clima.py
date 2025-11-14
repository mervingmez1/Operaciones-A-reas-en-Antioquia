import os
import random
import requests
from dotenv import load_dotenv

# Cargar API Key desde .env
load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

# ===========================
#   DATOS REALES DESDE API
# ===========================
def obtener_condiciones_meteorologicas(lat, lon):
    """
    Obtiene las condiciones meteorológicas desde OpenWeather API.
    Retorna un diccionario con temperatura, viento, visibilidad y nubosidad.
    """
    if API_KEY is None:
        print("⚠️ ADVERTENCIA: No se encontró API_KEY, usando datos simulados.")
        return obtener_condiciones_simuladas()

    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"
    )

    try:
        r = requests.get(url, timeout=5)
        data = r.json()

        # Conversión de unidades
        temperatura = data["main"]["temp"]
        viento = data["wind"]["speed"] * 3.6          # m/s → km/h
        vis_km = (data.get("visibility", 10000)) / 1000.0
        nubes = data["weather"][0]["description"].capitalize()

        return {
            "temperatura": temperatura,
            "viento": round(viento, 1),
            "visibilidad": round(vis_km, 1),
            "nubosidad": nubes
        }

    except Exception as e:
        print("❌ Error al obtener datos reales:", e)
        print("Usando condiciones simuladas.")
        return obtener_condiciones_simuladas()


# =================================
#     DATOS SIMULADOS (OFFLINE)
# =================================
def obtener_condiciones_simuladas():
    """Genera datos meteorológicos aleatorios."""
    condiciones = {
        "temperatura": round(random.uniform(15, 35), 1),
        "viento": round(random.uniform(0, 25), 1),  # km/h
        "visibilidad": round(random.uniform(1, 20), 1),  # km
        "nubosidad": random.choice(["Despejado", "Parcial", "Nublado", "Tormentoso"]),
    }
    return condiciones


# =======================================
#     CLASIFICACIÓN DE REGLAS DE VUELO
# =======================================
def determinar_reglas_vuelo(condiciones):
    """
    Determina si las condiciones son VFR, MVFR, IFR o LIFR.
    """

    vis_km = condiciones["visibilidad"]
    nubes = condiciones["nubosidad"].lower()

    # ---- LIFR ----
    if vis_km < 1:
        return "LIFR", "Condiciones extremadamente limitadas. Vuelo VFR prohibido."

    # ---- IFR ----
    if vis_km < 5:
        return "IFR", "Condiciones malas. Solo vuelo por instrumentos."

    # ---- MVFR ----
    if vis_km < 10 or "nublado" in nubes or "torment" in nubes:
        return "MVFR", "Condiciones marginales. Precaución: visibilidad o nubosidad reducida."

    # ---- VFR ----
    return "VFR", "Condiciones buenas para vuelo visual."


# ===============================
#  INDICADOR DE FUENTE DE DATOS
# ===============================
def fuente_datos():
    """Solo devuelve un texto indicando si se usa API o simulación."""
    return (
        "Datos meteorológicos obtenidos desde API externa (OpenWeather)"
        if API_KEY
        else "Datos meteorológicos simulados (modo offline)"
    )

# =======================================
#   EVALUACIÓN DE SEGURIDAD DEL VUELO
# =======================================

def es_condicion_segura(condiciones):
    """
    Determina si las condiciones son seguras para vuelo VFR.
    Retorna True/False.
    """
    categoria, _ = determinar_reglas_vuelo(condiciones)
    return categoria == "VFR" or categoria == "MVFR"


def analizar_condiciones_meteorologicas(condiciones):
    """
    Retorna un texto detallado usado por la interfaz.
    """
    categoria, mensaje = determinar_reglas_vuelo(condiciones)

    texto = (
        f"Clasificación meteorológica: {categoria}\n"
        f"{mensaje}\n\n"
        f"Temperatura: {condiciones['temperatura']} °C\n"
        f"Viento: {condiciones['viento']} km/h\n"
        f"Visibilidad: {condiciones['visibilidad']} km\n"
        f"Nubosidad: {condiciones['nubosidad']}"
    )

    return texto
