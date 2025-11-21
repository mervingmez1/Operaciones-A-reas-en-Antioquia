import tkinter as tk
from tkinter import ttk
from core.calculos import calcular_distancia_y_rumbo
from core.clima import (
    obtener_metar,
    determinar_reglas_vuelo,
    fuente_datos
)
from data.aeropuertos import AEROPUERTOS


class InterfazPlanificador:
    def __init__(self, root):
        self.root = root
        self.root.title("Planificador de Operaciones Aéreas")

        # Diccionario auxiliar: nombre visible → código ICAO
        self.nombres_a_codigos = {v["nombre"]: k for k, v in AEROPUERTOS.items()}

        # --- UI ---
        self.origen_label = ttk.Label(root, text="Aeropuerto de origen:")
        self.origen_label.grid(row=0, column=0, padx=5, pady=5)

        self.origen = ttk.Combobox(root, values=list(self.nombres_a_codigos.keys()))
        self.origen.grid(row=0, column=1, padx=5, pady=5)

        self.destino_label = ttk.Label(root, text="Aeropuerto de destino:")
        self.destino_label.grid(row=1, column=0, padx=5, pady=5)

        self.destino = ttk.Combobox(root, values=list(self.nombres_a_codigos.keys()))
        self.destino.grid(row=1, column=1, padx=5, pady=5)

        self.calcular_btn = ttk.Button(root, text="Planificar Ruta", command=self.planificar_ruta)
        self.calcular_btn.grid(row=2, column=0, columnspan=2, pady=10)

        # Área de resultado
        self.resultado = tk.Text(root, width=70, height=25)
        self.resultado.grid(row=3, column=0, columnspan=2)

        # Indicador de categoría (color)
        self.indicador = tk.Label(root, text="SIN DATOS", bg="gray", fg="white", width=20)
        self.indicador.grid(row=4, column=0, columnspan=2, pady=10)

    # --- Mostrar texto ---
    def mostrar_resultado(self, texto):
        self.resultado.delete(1.0, tk.END)
        self.resultado.insert(tk.END, texto)

    # --- Indicador visual de categoría ---
    def actualizar_indicador(self, categoria):
        colores = {
            "VFR": "green",
            "MVFR": "blue",
            "IFR": "red",
            "LIFR": "purple",
            "N/A": "gray"
        }
        self.indicador.config(
            text=categoria,
            bg=colores.get(categoria, "gray")
        )

    # -----------------------------------------
    # -------- LÓGICA PRINCIPAL ---------------
    # -----------------------------------------
    def planificar_ruta(self):
        o_nom, d_nom = self.origen.get(), self.destino.get()
        if not o_nom or not d_nom:
            self.mostrar_resultado("Selecciona origen y destino.")
            return
    
        o = AEROPUERTOS[self.nombres_a_codigos[o_nom]]
        d = AEROPUERTOS[self.nombres_a_codigos[d_nom]]
    
        dist_km, rumbo = calcular_distancia_y_rumbo(o, d)
        dist_nm = dist_km / 1.852
    
        icao_origen = self.nombres_a_codigos[o_nom]
        icao_destino = self.nombres_a_codigos[d_nom]
    
        # ======== METAR ORIGEN =========
        metar_origen = obtener_metar(icao_origen)
    
        # ======== METAR DESTINO =========
        metar_destino = obtener_metar(icao_destino)
    
        # --- Caso sin METAR en origen (lo más importante) ---
        if not metar_origen:
            self.mostrar_resultado(
                f"✈️ {o_nom} → {d_nom}\n"
                f"📍 Distancia: {dist_km:.1f} km ({dist_nm:.1f} NM)\n"
                f"🧭 Rumbo: {rumbo:.1f}°\n\n"
                "⚠️ No hay METAR disponible para el aeropuerto de ORIGEN."
            )
            self.actualizar_indicador("N/A")
            return
    
        # ======== Clasificación basada SOLO en METAR ORIGEN ========
        cat, desc_cat = determinar_reglas_vuelo(metar_origen)
    
        # ======== Preparar texto para el destino ========
        if metar_destino:
            texto_destino = (
                f"🌦️ Condiciones en DESTINO ({d_nom}):\n"
                f"   • Temp: {metar_destino.get('temperatura', 'N/A')}°C\n"
                f"   • Viento: {metar_destino.get('viento', 'N/A')} kt\n"
                f"   • Visibilidad: {metar_destino.get('visibilidad', 'N/A')} NM\n"
                f"   • QNH: {metar_destino.get('presion', 'N/A')} hPa\n"
                f"   • Nubosidad: {metar_destino.get('nubosidad', 'N/A')}\n\n"
                f"METAR RAW (Destino):\n{metar_destino.get('raw_text', '(no disponible)')}\n\n"
            )
        else:
            texto_destino = (
                f"🌦️ Condiciones en DESTINO ({d_nom}):\n"
                f"   ⚠️ No hay METAR disponible.\n\n"
            )
    
        # ======== TEXTO PRINCIPAL ========
        texto = (
            f"✈️ Ruta: {o_nom} → {d_nom}\n"
            f"📍 Distancia: {dist_km:.1f} km ({dist_nm:.1f} NM)\n"
            f"🧭 Rumbo: {rumbo:.1f}°\n\n"
            f"🌦️ Condiciones en ORIGEN ({o_nom}):\n"
            f"   • Temp: {metar_origen.get('temperatura', 'N/A')}°C\n"
            f"   • Viento: {metar_origen.get('viento', 'N/A')} kt\n"
            f"   • Visibilidad: {metar_origen.get('visibilidad', 'N/A')} NM\n"
            f"   • QNH: {metar_origen.get('presion', 'N/A')} hPa\n\n"
            f"📏 Clasificación: {cat}\n"
            f"{desc_cat}\n\n"
            f"METAR RAW (Origen):\n{metar_origen.get('raw_text', '(no disponible)')}\n\n"
            f"{texto_destino}"
            f"Fuente: CheckWX API"
        )
    
        self.mostrar_resultado(texto)
        self.actualizar_indicador(cat)
    
        # Alertas visuales
        if cat in ["VFR", "MVFR"]:
            messagebox.showinfo("Condición de vuelo", "🟢 Condiciones seguras para vuelo visual.")
        else:
            messagebox.showwarning("Condición de vuelo", "🔴 Condiciones NO seguras para vuelo visual.")
    
    