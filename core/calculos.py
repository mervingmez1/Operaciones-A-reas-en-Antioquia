from geopy.distance import geodesic
from data.aeropuertos import AEROPUERTOS

def distancia_entre_aeropuertos(cod1: str, cod2: str) -> float:
    a1, a2 = AEROPUERTOS[cod1], AEROPUERTOS[cod2]
    return geodesic((a1["lat"], a1["lon"]), (a2["lat"], a2["lon"])).kilometers

