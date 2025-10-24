from geopy.distance import geodesic
from data.aeropuertos import AEROPUERTOS
import math


#def distancia_entre_aeropuertos(cod1: str, cod2: str) -> float:
#    a1, a2 = AEROPUERTOS[cod1], AEROPUERTOS[cod2]
#    return geodesic((a1["lat"], a1["lon"]), (a2["lat"], a2["lon"])).kilometers


#Función con un error menor al 0.5%
def calcular_distancia(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos puntos geográficos usando la fórmula de Haversine.
    Retorna la distancia en kilómetros (km).
    """
    # Radio de la Tierra en km
    R = 6371.0

    # Convertir coordenadas a radianes
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    # Diferencias
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distancia = R * c
    return distancia


import math

def calcular_distancia_y_rumbo(origen: dict, destino: dict):
    """
    Calcula la distancia (km) y el rumbo inicial (grados) entre dos aeropuertos.
    Los parámetros deben ser diccionarios con 'lat' y 'lon' en grados decimales.
    """
    # Radio de la Tierra (km)
    R = 6371.0

    # Convertir a radianes
    lat1 = math.radians(origen["lat"])
    lon1 = math.radians(origen["lon"])
    lat2 = math.radians(destino["lat"])
    lon2 = math.radians(destino["lon"])

    # Diferencias
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Fórmula de Haversine
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))
    distancia = R * c

    # Rumbo inicial
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    rumbo = math.degrees(math.atan2(y, x))
    rumbo = (rumbo + 360) % 360  # Normalizar a 0–360°

    return distancia, rumbo

    

