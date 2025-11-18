from data.aeropuertos import AEROPUERTOS
from core.calculos import calcular_distancia_y_rumbo
import tkinter as tk
from ui.interfaz import InterfazPlanificador
#Ejecuta "pip install -r requirements.txt"

if __name__ == "__main__":
    # MODO DE PRUEBA (activa o comenta según necesites)
    modo_prueba = False  # cambiar a True para ejecutar solo el cálculo por consola

    if modo_prueba:
        origen = AEROPUERTOS["SKRG"]
        destino = AEROPUERTOS["SKMD"]

        distancia, rumbo = calcular_distancia_y_rumbo(origen, destino)

        print(f"Distancia entre {origen['nombre']} y {destino['nombre']}: {distancia:.2f} km")
        print(f"Rumbo inicial: {rumbo:.1f}°")

    else:
        # Iniciar interfaz gráfica
        root = tk.Tk()
        app = InterfazPlanificador(root)
        root.mainloop()
