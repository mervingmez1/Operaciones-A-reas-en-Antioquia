from core.calculos import distancia_entre_aeropuertos
from data.aeropuertos import AEROPUERTOS

if __name__ == "__main__":
    origen, destino = "SKMD", "SKRG"
    distancia = distancia_entre_aeropuertos(origen, destino)
    print(f"Distancia entre {AEROPUERTOS[origen]['nombre']} y {AEROPUERTOS[destino]['nombre']}: {distancia:.2f} km")
