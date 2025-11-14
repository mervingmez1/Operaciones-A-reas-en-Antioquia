# core/mapas.py
import os
import time
import webbrowser
from pathlib import Path
import folium

def _ruta_archivo_html(nombre="ruta"):
    """Generar ruta de archivo en carpeta ./maps/ con timestamp"""
    base = Path.cwd() / "maps"
    base.mkdir(exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    return str(base / f"{nombre}_{ts}.html")


def generar_mapa_ruta(origen, destino, distancia_km=None, rumbo_deg=None, abrir_en_navegador=True):
    """
    Genera un mapa folium con marcador de origen y destino y una polyline entre ellos.
    origen/destino: diccionarios con 'lat', 'lon', 'nombre'
    distancia_km: (opcional) distancia calculada
    rumbo_deg: (opcional) rumbo inicial para mostrar en la info
    Si abrir_en_navegador=True, abre el HTML en el navegador por defecto.
    Retorna la ruta del archivo HTML generado.
    """
    lat1, lon1 = origen["lat"], origen["lon"]
    lat2, lon2 = destino["lat"], destino["lon"]

    # Centrar mapa en el punto medio
    centro_lat = (lat1 + lat2) / 2.0
    centro_lon = (lon1 + lon2) / 2.0

    m = folium.Map(location=[centro_lat, centro_lon], zoom_start=8, control_scale=True)

    # Popups informativos
    popup_origen = f"{origen['nombre']} ({lat1:.4f}, {lon1:.4f})"
    popup_destino = f"{destino['nombre']} ({lat2:.4f}, {lon2:.4f})"

    if distancia_km is not None:
        popup_origen += f"<br>Distancia: {distancia_km:.2f} km"
        popup_destino += f"<br>Distancia: {distancia_km:.2f} km"
    if rumbo_deg is not None:
        popup_origen += f"<br>Rumbo inicial: {rumbo_deg:.1f}°"

    folium.Marker([lat1, lon1], popup=folium.Popup(popup_origen, max_width=300), tooltip="Origen", icon=folium.Icon(color="green", icon="plane")).add_to(m)
    folium.Marker([lat2, lon2], popup=folium.Popup(popup_destino, max_width=300), tooltip="Destino", icon=folium.Icon(color="red", icon="flag")).add_to(m)

    # Línea de la ruta
    folium.PolyLine(locations=[[lat1, lon1], [lat2, lon2]], weight=4, color="#3388ff", opacity=0.8).add_to(m)

    # Ajustar vista para incluir ambos puntos con padding
    sw = [min(lat1, lat2), min(lon1, lon2)]
    ne = [max(lat1, lat2), max(lon1, lon2)]
    m.fit_bounds([sw, ne], padding=(30, 30))

    # Añadir control de capas ligera
    folium.LayerControl().add_to(m)

    archivo = _ruta_archivo_html("ruta")
    m.save(archivo)

    if abrir_en_navegador:
        webbrowser.open_new_tab(f"file://{os.path.abspath(archivo)}")

    return archivo
