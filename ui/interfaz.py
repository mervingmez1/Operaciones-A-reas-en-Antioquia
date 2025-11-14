import tkinter as tk
from tkinter import ttk, messagebox
from data.aeropuertos import AEROPUERTOS
from core.calculos import calcular_distancia_y_rumbo
from core.clima import (
    obtener_condiciones_meteorologicas,
    es_condicion_segura,
    determinar_reglas_vuelo,
    fuente_datos
)
from core.mapas import generar_mapa_ruta


class InterfazPlanificador:
    def __init__(self, master):
        self.master = master
        self.master.title("Planificador de Rutas Aéreas - Antioquia")
        self.master.geometry("900x650")

        ttk.Label(master, text="Planificador de Rutas Aéreas", font=("Helvetica", 18, "bold")).pack(pady=20)

        # Diccionario nombre -> código
        self.nombres_a_codigos = {v["nombre"]: k for k, v in AEROPUERTOS.items()}
        nombres_aeropuertos = list(self.nombres_a_codigos.keys())

        # --- Selección de aeropuertos ---
        frame_aeropuertos = ttk.LabelFrame(master, text="Selección de Aeropuertos", padding=20)
        frame_aeropuertos.pack(fill="x", padx=20, pady=10)

        ttk.Label(frame_aeropuertos, text="Aeropuerto de Origen:").grid(row=0, column=0, sticky="w")
        self.origen = ttk.Combobox(frame_aeropuertos, values=nombres_aeropuertos, state="readonly")
        self.origen.grid(row=0, column=1, padx=10)
        if nombres_aeropuertos:
            self.origen.current(0)

        ttk.Label(frame_aeropuertos, text="Aeropuerto de Destino:").grid(row=1, column=0, sticky="w")
        self.destino = ttk.Combobox(frame_aeropuertos, values=nombres_aeropuertos, state="readonly")
        self.destino.grid(row=1, column=1, padx=10)
        if len(nombres_aeropuertos) > 1:
            self.destino.current(1)

        # --- Botones ---
        frame_botones = ttk.Frame(master)
        frame_botones.pack(pady=10)
        ttk.Button(frame_botones, text="Planificar Ruta", command=self.planificar_ruta).grid(row=0, column=0, padx=6)
        ttk.Button(frame_botones, text="Mostrar Mapa", command=self.mostrar_mapa).grid(row=0, column=1, padx=6)

        # --- Resultado ---
        self.resultado = tk.Text(master, height=14, width=100)
        self.resultado.pack(pady=10)

        # --- Indicador visual ---
        self.indicador_estado = tk.Label(
            master,
            text="",
            font=("Helvetica", 16, "bold"),
            width=40,
            pady=12
        )
        self.indicador_estado.pack(pady=10)

    # ==============================================
    #   Función para mostrar resultados
    # ==============================================
    def mostrar_resultado(self, texto):
        self.resultado.delete("1.0", tk.END)
        self.resultado.insert(tk.END, texto)

    # ==============================================
    #   Indicador visual VFR / MVFR / IFR / LIFR
    # ==============================================
    def actualizar_indicador(self, reglas):
        colores = {
            "VFR": "#4CAF50",
            "MVFR": "#FFCA28",
            "IFR": "#FF7043",
            "LIFR": "#D32F2F"
        }

        textos = {
            "VFR": "🟢 Condiciones VFR (Buenas)",
            "MVFR": "🟡 Condiciones MVFR (Marginal)",
            "IFR": "🟠 Condiciones IFR (Instrumentales)",
            "LIFR": "🔴 Condiciones LIFR (Muy pobres)"
        }

        color = colores.get(reglas, "#888888")
        texto = textos.get(reglas, "Estado desconocido")

        self.indicador_estado.config(text=texto, bg=color, fg="white")

    # ==============================================
    #         Lógica principal
    # ==============================================
    def planificar_ruta(self):
        origen_nombre = self.origen.get()
        destino_nombre = self.destino.get()

        if not origen_nombre or not destino_nombre:
            self.mostrar_resultado("Por favor selecciona un origen y un destino.")
            return

        origen_codigo = self.nombres_a_codigos[origen_nombre]
        destino_codigo = self.nombres_a_codigos[destino_nombre]
        origen = AEROPUERTOS[origen_codigo]
        destino = AEROPUERTOS[destino_codigo]

        # Cálculo de distancia y rumbo
        distancia, rumbo = calcular_distancia_y_rumbo(origen, destino)

        # Meteorología (API o simulada)
        condiciones = obtener_condiciones_meteorologicas(origen["lat"], origen["lon"])

        # Estado VFR / IFR básico
        segura = es_condicion_segura(condiciones)
        estado_seguridad = "🟢 SEGURA (VFR)" if segura else "🔴 NO SEGURA (IFR recomendado)"

        # Reglas de vuelo
        reglas, descripcion_reglas = determinar_reglas_vuelo(condiciones)

        # Actualizar indicador visual
        self.actualizar_indicador(reglas)

        # Mostrar resultado
        resultado = (
            f"✈️ Ruta: {origen['nombre']} → {destino['nombre']}\n"
            f"📍 Distancia: {distancia:.2f} km\n"
            f"🧭 Rumbo inicial: {rumbo:.1f}°\n\n"

            f"🌦️ Condiciones meteorológicas:\n"
            f"   • Temperatura: {condiciones['temperatura']} °C\n"
            f"   • Viento: {condiciones['viento']} km/h\n"
            f"   • Visibilidad: {condiciones['visibilidad']} km\n"
            f"   • Nubosidad: {condiciones['nubosidad']}\n\n"

            f"🛫 Estado VFR/IFR: {estado_seguridad}\n"
            f"📏 Clasificación: {reglas}\n"
            f"{descripcion_reglas}\n\n"

            f"📘 Fuente de datos: {fuente_datos()}"
        )

        self.mostrar_resultado(resultado)

        if segura:
            messagebox.showinfo("Condición de vuelo", "🟢 Condiciones SEGURAS para vuelo visual (VFR).")
        else:
            messagebox.showwarning("Condición de vuelo", "🔴 Condiciones NO SEGURAS. Se recomienda vuelo IFR.")

    # ==============================================
    #      NUEVO MÉTODO: MOSTRAR MAPA
    # ==============================================
    def mostrar_mapa(self):
        origen_nombre = self.origen.get()
        destino_nombre = self.destino.get()

        if not origen_nombre or not destino_nombre:
            messagebox.showwarning("Mapa", "Selecciona origen y destino primero.")
            return

        origen_codigo = self.nombres_a_codigos[origen_nombre]
        destino_codigo = self.nombres_a_codigos[destino_nombre]
        origen = AEROPUERTOS[origen_codigo]
        destino = AEROPUERTOS[destino_codigo]

        distancia, rumbo = calcular_distancia_y_rumbo(origen, destino)

        try:
            archivo = generar_mapa_ruta(
                origen,
                destino,
                distancia_km=distancia,
                rumbo_deg=rumbo,
                abrir_en_navegador=True
            )
            messagebox.showinfo("Mapa", f"Mapa generado: {archivo}\nSe abrió en tu navegador.")
        except Exception as e:
            messagebox.showerror("Error mapa", f"No se pudo generar el mapa:\n{e}")


# ==============================================
#           EJECUCIÓN PRINCIPAL
# ==============================================
if __name__ == "__main__":
    root = tk.Tk()
    app = InterfazPlanificador(root)
    root.mainloop()
