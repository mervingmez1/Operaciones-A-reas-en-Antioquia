import os
import requests
from dotenv import load_dotenv

load_dotenv()

CHECKWX_KEY = os.getenv("CHECKWX_API_KEY")


# ============================================================
# 1) Obtener METAR REAL desde CheckWX
# ============================================================

def obtener_metar(icao: str):
    """
    Consulta METAR desde CheckWX y lo devuelve en un diccionario normalizado.
    """

    if not CHECKWX_KEY:
        print("[ERROR] No existe clave CHECKWX_API_KEY en .env")
        return None

    url = f"https://api.checkwx.com/metar/{icao}/decoded"

    try:
        r = requests.get(url, headers={"X-API-Key": CHECKWX_KEY}, timeout=10)

        if r.status_code != 200:
            print(f"[CheckWX] Error HTTP {r.status_code} para {icao}")
            return None

        data = r.json()

        if not data.get("data"):
            print(f"[CheckWX] Sin datos METAR para {icao}")
            return None

        metar = data["data"][0]

        # --- extraer datos ---
        temp = metar.get("temperature", {}).get("celsius")
        wind = metar.get("wind", {}).get("speed_kts")
        vis_m = metar.get("visibility", {}).get("meters")
        qnh = metar.get("barometer", {}).get("hpa")

        # Convertir visibilidad a millas náuticas
        vis_nm = round(vis_m / 1852, 1) if vis_m else None

        # Nubosidad
        sky = metar.get("sky", [])
        if isinstance(sky, list) and len(sky) > 0:
            nub = sky[0].get("condition", "Despejado")
        else:
            nub = "Despejado"

        return {
            "temperatura": temp,
            "viento": wind,
            "visibilidad": vis_nm,
            "presion": qnh,
            "nubosidad": nub,
            "raw_text": metar.get("raw_text", "N/A"),
        }

    except Exception as e:
        print(f"[obtener_metar] Error para {icao}: {e}")
        return None


# ============================================================
# 2) Clasificación de reglas de vuelo (compatible con tu interfaz)
# ============================================================

def determinar_reglas_vuelo(cond):
    vis = cond.get("visibilidad")

    if vis is None:
        return "N/A", "No hay visibilidad reportada"

    if vis < 1:
        return "LIFR", "Condiciones extremadamente limitadas."
    if vis < 3:
        return "IFR", "Condiciones solo para vuelo por instrumentos."
    if vis < 5:
        return "MVFR", "Condiciones marginales."
    return "VFR", "Buenas condiciones visuales."


# ============================================================
# 3) Texto detallado usado en posibles reportes
# ============================================================

def analizar_condiciones_meteorologicas(cond):
    categoria, mensaje = determinar_reglas_vuelo(cond)

    return (
        f"Clasificación meteorológica: {categoria}\n"
        f"{mensaje}\n\n"
        f"Temperatura: {cond.get('temperatura', 'N/A')} °C\n"
        f"Viento: {cond.get('viento', 'N/A')} kt\n"
        f"Visibilidad: {cond.get('visibilidad', 'N/A')} NM\n"
        f"Presión: {cond.get('presion', 'N/A')} hPa\n"
        f"Nubosidad: {cond.get('nubosidad', 'N/A')}"
    )


# ============================================================
# 4) Fuente de datos mostrada en la interfaz
# ============================================================

def fuente_datos():
    if CHECKWX_KEY:
        return "Datos METAR reales vía CheckWX API"
    else:
        return "No hay API configurada"
