import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import json

from data.aeropuertos import AEROPUERTOS
from core.calculos import calcular_distancia_y_rumbo
from core.clima import (
    obtener_condiciones_meteorologicas,
    es_condicion_segura,
    determinar_reglas_vuelo,
    fuente_datos
)
from core.mapas import generar_mapa_ruta

# Ruta para persistir última selección (opcional)
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".planificador_config.json")


class InterfazPlanificador:
    def __init__(self, master):
        # --- ventana principal ---
        self.master = master
        self.master.title("Planificador de Rutas Aéreas - Antioquia")
        self.master.geometry("1100x700")

        # Cargar config previa (si existe)
        self.config = self._cargar_config()

        # --- layout: contenedor principal con sidebar + main area ---
        self.contenedor = ttk.Frame(master)
        self.contenedor.pack(fill="both", expand=True)

        # -----------------------
        # SIDEBAR (IZQUIERDA) - añadida
        # -----------------------
        sidebar = ttk.Frame(self.contenedor, width=280, padding=(10,10))
        sidebar.pack(side="left", fill="y")

        # Título sidebar
        ttk.Label(sidebar, text="Aeropuertos", font=("Helvetica", 12, "bold")).pack(pady=(4,6))

        # Campo de búsqueda
        self.search_var = tk.StringVar()
        self.entry_search = ttk.Entry(sidebar, textvariable=self.search_var)
        self.entry_search.pack(fill="x", padx=6, pady=(0,6))
        # Filtrar al escribir
        self.search_var.trace_add("write", lambda *a: self.filtrar_lista())

        # Frame para listbox + scrollbar
        list_frame = ttk.Frame(sidebar)
        list_frame.pack(fill="both", expand=False, padx=6)

        # Diccionario nombre -> código (usado en comboboxes también)
        self.nombres_a_codigos = {v["nombre"]: k for k, v in AEROPUERTOS.items()}
        nombres_aeropuertos = sorted(list(self.nombres_a_codigos.keys()))

        # Listbox con scrollbar
        self.lista_aeropuertos = tk.Listbox(list_frame, height=14, activestyle="dotbox")
        scrollbar = ttk.Scrollbar(list_frame, command=self.lista_aeropuertos.yview)
        self.lista_aeropuertos.config(yscrollcommand=scrollbar.set)
        self.lista_aeropuertos.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Poblar listbox
        for nombre in nombres_aeropuertos:
            self.lista_aeropuertos.insert(tk.END, nombre)

        # Evento seleccion listbox -> mostrar info aeropuerto
        self.lista_aeropuertos.bind("<<ListboxSelect>>", self.mostrar_info_aeropuerto)

        # Etiqueta para foto del aeropuerto
        self.label_foto = tk.Label(sidebar, bg="#EEEEEE")
        self.label_foto.pack(pady=8)

        # Texto info del aeropuerto
        self.info_aeropuerto = tk.Label(sidebar, bg="#EEEEEE", justify="left", font=("Helvetica", 9))
        self.info_aeropuerto.pack(padx=8, pady=(0,8))

        # Botones: usar seleccionado como origen/destino
        ttk.Button(sidebar, text="Usar como Origen", command=self.seleccionar_origen).pack(pady=4, padx=8, fill="x")
        ttk.Button(sidebar, text="Usar como Destino", command=self.seleccionar_destino).pack(pady=4, padx=8, fill="x")

        # Guardar última imagen para evitar GC
        self.img_tk = None

        # -----------------------
        # AREA PRINCIPAL (DERECHA) - funcionalidad original
        # -----------------------
        main_area = ttk.Frame(self.contenedor, padding=(10,10))
        main_area.pack(side="right", fill="both", expand=True)

        ttk.Label(main_area, text="Planificador de Rutas Aéreas", font=("Helvetica", 18, "bold")).pack(pady=20)

        # --- Selección de aeropuertos (comboboxes) ---
        frame_aeropuertos = ttk.LabelFrame(main_area, text="Selección de Aeropuertos", padding=12)
        frame_aeropuertos.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame_aeropuertos, text="Aeropuerto de Origen:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        self.origen = ttk.Combobox(frame_aeropuertos, values=nombres_aeropuertos, state="readonly")
        self.origen.grid(row=0, column=1, padx=10, pady=6)

        ttk.Label(frame_aeropuertos, text="Aeropuerto de Destino:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        self.destino = ttk.Combobox(frame_aeropuertos, values=nombres_aeropuertos, state="readonly")
        self.destino.grid(row=1, column=1, padx=10, pady=6)

        # Restaurar última selección desde config (si existe)
        if nombres_aeropuertos:
            try:
                if self.config.get("origen") in nombres_aeropuertos:
                    self.origen.set(self.config.get("origen"))
                else:
                    self.origen.current(0)
            except Exception:
                self.origen.current(0)

        if len(nombres_aeropuertos) > 1:
            try:
                if self.config.get("destino") in nombres_aeropuertos:
                    self.destino.set(self.config.get("destino"))
                else:
                    self.destino.current(1)
            except Exception:
                self.destino.current(1)

        # --- Botones principales (originales) ---
        frame_botones = ttk.Frame(main_area)
        frame_botones.pack(pady=8)
        ttk.Button(frame_botones, text="Planificar Ruta", command=self.planificar_ruta).grid(row=0, column=0, padx=6)
        ttk.Button(frame_botones, text="Mostrar Mapa", command=self.mostrar_mapa).grid(row=0, column=1, padx=6)

        # --- Resultado original ---
        self.resultado = tk.Text(main_area, height=14, width=100)
        self.resultado.pack(pady=10)

        # --- Indicador visual (original) ---
        self.indicador_estado = tk.Label(
            main_area,
            text="",
            font=("Helvetica", 16, "bold"),
            width=40,
            pady=12
        )
        self.indicador_estado.pack(pady=10)

        # En cerrar ventana persistir configuración
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

    # ==============================================
    #   Configuración persistente (guardar / cargar)
    # ==============================================
    def _cargar_config(self):
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return {}

    def _guardar_config(self):
        try:
            data = {
                "origen": self.origen.get(),
                "destino": self.destino.get()
            }
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception:
            pass

    def _on_close(self):
        # Guardar configuración y cerrar
        self._guardar_config()
        self.master.destroy()

    # ==============================================
    #   Función para mostrar resultados (original)
    # ==============================================
    def mostrar_resultado(self, texto):
        self.resultado.delete("1.0", tk.END)
        self.resultado.insert(tk.END, texto)

    # ==============================================
    #   Indicador visual VFR / MVFR / IFR / LIFR (original)
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
    #         Lógica principal (original)
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

        # Mostrar resultado (formato original)
        resultado = (
            f"✈️ Ruta: {origen['nombre']} → {destino['nombre']}\n"
            f"📍 Distancia: {distancia:.2f} km\n"
            f"🧭 Rumbo inicial: {rumbo:.1f}°\n\n"

            f"🌦️ Condiciones meteorológicas:\n"
            f"   • Temperatura: {condiciones.get('temperatura', 'N/A')} °C\n"
            f"   • Viento: {condiciones.get('viento', 'N/A')} km/h\n"
            f"   • Visibilidad: {condiciones.get('visibilidad', 'N/A')} km\n"
            f"   • Nubosidad: {condiciones.get('nubosidad', 'N/A')}\n\n"

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
    #      MOSTRAR MAPA (original)
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
    #   Mostrar info desde la lista lateral (nueva)
    # ==============================================
    def mostrar_info_aeropuerto(self, event):
        seleccion = self.lista_aeropuertos.curselection()
        if not seleccion:
            return

        nombre = self.lista_aeropuertos.get(seleccion[0])
        codigo = self.nombres_a_codigos.get(nombre)
        if codigo is None:
            return
        data = AEROPUERTOS[codigo]

        # Actualizar texto
        texto = (
            f"📍 {data.get('nombre','N/A')}\n"
            f"✈️ Código: {codigo}\n"
            f"🌎 Lat: {data.get('lat','N/A')}\n"
            f"🌍 Lon: {data.get('lon','N/A')}\n"
            f"⛰️ Elevación: {data.get('elev', 'N/A')} ft"
        )
        self.info_aeropuerto.config(text=texto)

        # Cargar foto (opcional)
        self.cargar_foto(codigo)

    # ==============================================
    # Filtrar lista (nueva)
    # ==============================================
    def filtrar_lista(self):
        q = self.search_var.get().strip().lower()
        self.lista_aeropuertos.delete(0, tk.END)
        for nombre in sorted(self.nombres_a_codigos.keys()):
            if q == "" or q in nombre.lower():
                self.lista_aeropuertos.insert(tk.END, nombre)

    # ==============================================
    # Cargar foto del aeropuerto (nueva)
    # ==============================================
    def cargar_foto(self, codigo):
        ruta = os.path.join("assets", f"{codigo}.jpg")

        if not os.path.exists(ruta):
            ruta = os.path.join("assets", "default.jpg")

        try:
            img = Image.open(ruta)
            img = img.resize((200, 150))
            self.img_tk = ImageTk.PhotoImage(img)
            self.label_foto.config(image=self.img_tk)
        except Exception:
            # Imagen no disponible -> limpiar
            self.label_foto.config(image="")
            self.img_tk = None

    # ==============================================
    #  Seleccionar aeropuerto desde el panel lateral (nuevos)
    # ==============================================
    def seleccionar_origen(self):
        seleccion = self.lista_aeropuertos.curselection()
        if not seleccion:
            messagebox.showwarning("Origen", "Selecciona un aeropuerto de la lista.")
            return

        nombre = self.lista_aeropuertos.get(seleccion[0])
        self.origen.set(nombre)
        messagebox.showinfo("Origen seleccionado", f"Origen establecido: {nombre}")
        # Guardar selección parcial
        self._guardar_config()

    def seleccionar_destino(self):
        seleccion = self.lista_aeropuertos.curselection()
        if not seleccion:
            messagebox.showwarning("Destino", "Selecciona un aeropuerto de la lista.")
            return

        nombre = self.lista_aeropuertos.get(seleccion[0])
        self.destino.set(nombre)
        messagebox.showinfo("Destino seleccionado", f"Destino establecido: {nombre}")
        # Guardar selección parcial
        self._guardar_config()


# ==============================================
#           EJECUCIÓN PRINCIPAL (para pruebas)
# ==============================================
if __name__ == "__main__":
    root = tk.Tk()
    app = InterfazPlanificador(root)
    root.mainloop()
