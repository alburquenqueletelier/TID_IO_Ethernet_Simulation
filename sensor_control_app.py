import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import psutil
import json
from datetime import datetime
from collections import defaultdict, deque
import re
import threading
import time
import csv
from scapy.all import Ether, Raw, sendp
import os
import json
import math


appendix_dict = {
    "X_00_CPU": b"\x00",
    "X_02_TestTrigger": b"\x02",
    "X_03_RO_Single": b"\x03",
    "X_04_RO_ON": b"\x04",
    "X_05_RO_OFF": b"\x05",
    "X_08_DIAG_": b"\x08",
    "X_09_DIAG_DIS": b"\x09",
    "X_F9_TTrig_Global": b"\xf9",
    "X_FA_TTrig_Local": b"\xfa",
    "X_FB_TTrig_Auto_EN": b"\xfb",
    "X_FC_TTrig_Auto_DIS": b"\xfc",
    "X_FF_Reset": b"\xff",
    "X_20_PwrDwnb_TOP_ON": b"\x20",
    "X_21_PwrDwnb_TOP_OFF": b"\x21",
    "X_22_PwrDwnb_BOT_ON": b"\x22",
    "X_23_PwrDwnb_BOT_OFF": b"\x23",
    "X_24_PwrEN_2V4A_ON": b"\x24",
    "X_25_PwrEN_2V4A_OFF": b"\x25",
    "X_26_PwrEN_2V4D_ON": b"\x26",
    "X_27_PwrEN_2V4D_OFF": b"\x27",
    "X_28_PwrEN_3V1_ON": b"\x28",
    "X_29_PwrEN_3V1_OFF": b"\x29",
    "X_2A_PwrEN_1V8A_ON": b"\x2a",
    "X_2B_PwrEN_1V8A_OFF": b"\x2b",
    "X_E0_FanSpeed0_Low": b"\xe0",
    "X_E1_FanSpeed0_High": b"\xe1",
    "X_E2_FanSpeed1_Low": b"\xe2",
    "X_E3_FanSpeed1_High": b"\xe3",
}
db_json = "db.json"


class McControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de Microcontroladores y Micro Controladores")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")

        # Comandos
        self.commands = appendix_dict

        # Variables de estado
        self.admin_in = False
        self.running = False

        # Variable para controlar cancelación de envío
        self.sending_commands = False
        self.cancel_sending = False

        # Contadores y estadísticas
        self.mc_available = {}  # keys: mac_source, values: interfaces
        self.mc_registered = (
            {}
        )  # keys: mac_source, values: dict {  mac_destiny, interface_destiny, label, last_state{} }
        self.frames_sent = 0
        self.frames_received = 0

        # Estado de asociaciones PET
        self.pet_associations = {}  # {pet_num: {"mc": mac_destiny, "enable": boolean}}
        for i in range(1, 11):
            self.pet_associations[i] = {"mc": None, "enabled": None}

        self.init_database()

        self.create_main_interface()

    def setup_drag_and_drop(self, row_frame, cmd_name):
        """Configura drag and drop para una fila de comando"""
        self.dragging = False
        self.drag_source = None
        self.drag_placeholder = None

        # Bind events solo al frame de la fila (no a botones ni checkboxes)
        row_frame.bind("<Enter>", lambda e: row_frame.config(cursor="hand1"))
        row_frame.bind("<Leave>", lambda e: row_frame.config(cursor=""))
        row_frame.bind("<Button-1>", lambda e: self.start_drag(e, row_frame, cmd_name))
        row_frame.bind("<B1-Motion>", lambda e: self.do_drag(e, row_frame))
        row_frame.bind("<ButtonRelease-1>", lambda e: self.end_drag(e, row_frame))

    def start_drag(self, event, row_frame, cmd_name):
        """Inicia el arrastre"""
        # Solo iniciar si no se clickeó en un botón o checkbox
        widget = event.widget
        if isinstance(widget, (tk.Button, tk.Checkbutton)):
            return

        self.dragging = True
        self.drag_source = (row_frame, cmd_name)
        self.drag_start_y = event.y_root

        # Cambiar apariencia de la fila que se está arrastrando
        row_frame.config(relief="raised", borderwidth=3, bg="#e3f2fd")

    def do_drag(self, event, row_frame):
        """Maneja el movimiento durante el arrastre"""
        if not self.dragging:
            return

        # Calcular sobre qué fila está el cursor
        for frame_data in self.command_rows:
            frame = frame_data["frame"]
            frame_y = frame.winfo_rooty()
            frame_height = frame.winfo_height()

            if frame_y <= event.y_root <= frame_y + frame_height:
                # Resaltar la fila sobre la que está
                if frame != row_frame:
                    frame.config(bg="#fff3e0")
            else:
                # Restaurar color original
                if frame != row_frame:
                    frame.config(bg="white")

    def end_drag(self, event, row_frame):
        """Finaliza el arrastre y reordena"""
        if not self.dragging:
            return

        self.dragging = False

        # Restaurar apariencia
        row_frame.config(relief="ridge", borderwidth=1, bg="white")

        # Encontrar sobre qué fila se soltó
        target_row = None
        target_index = None

        for i, frame_data in enumerate(self.command_rows):
            frame = frame_data["frame"]
            frame.config(bg="white")  # Restaurar todos

            frame_y = frame.winfo_rooty()
            frame_height = frame.winfo_height()

            if frame_y <= event.y_root <= frame_y + frame_height:
                target_row = frame_data
                target_index = i
                break

        # Si se soltó sobre otra fila, reordenar
        if target_row and target_row["cmd_name"] != self.drag_source[1]:
            self.reorder_commands(self.drag_source[1], target_row["cmd_name"])

        self.drag_source = None

    def reorder_commands(self, source_cmd, target_cmd):
        """Reordena los comandos en la lista y actualiza la UI"""
        selected_mc_display = self.mc_var.get()
        selected_mc = self.get_mac_from_selection(selected_mc_display) if selected_mc_display else None

        # Buscar el MC seleccionado
        mc_data = None
        for data in self.mc_registered.values():
            if data.get("mac_destiny") == selected_mc:
                mc_data = data
                break

        if not mc_data:
            return

        # Reordenar en la lista visual
        source_idx = None
        target_idx = None
        for i, row_data in enumerate(self.command_rows):
            if row_data["cmd_name"] == source_cmd:
                source_idx = i
            if row_data["cmd_name"] == target_cmd:
                target_idx = i

        if source_idx is None or target_idx is None:
            return

        item = self.command_rows.pop(source_idx)
        self.command_rows.insert(target_idx, item)

        # Reordenar también en el MC específico
        configs_list = list(mc_data["command_configs"].items())
        config_item = configs_list.pop(source_idx)
        configs_list.insert(target_idx, config_item)
        mc_data["command_configs"] = dict(configs_list)

        # Actualizar la UI
        self.rebuild_command_table()
        self.add_response(
            f"✓ Orden actualizado: {source_cmd} movido a posición de {target_cmd}"
        )

    def rebuild_command_table(self):
        """Reconstruye la tabla de comandos con el nuevo orden y carga last_state según MC seleccionado"""
        # Guardar estado actual de comandos antes de destruir filas
        prev_states = {}
        for cmd_name, cmd_state in self.commands_state.items():
            prev_states[cmd_name] = {
                "enabled": cmd_state["enabled"].get() if "enabled" in cmd_state else False,
                "state": cmd_state.get("state"),
            }

        # Destruir todas las filas actuales
        for row_data in self.command_rows:
            row_data["frame"].destroy()
        self.command_rows.clear()

        # Obtener el MC destino seleccionado
        selected_mc_display = self.mc_var.get()
        selected_mc = self.get_mac_from_selection(selected_mc_display) if selected_mc_display else None

        # Buscar el MC seleccionado y su orden de comandos
        mc_data = None
        for data in self.mc_registered.values():
            if data.get("mac_destiny") == selected_mc:
                mc_data = data
                break

        # Cargar delta_time si existe en el MC
        if mc_data and "delta_time" in mc_data:
            self.delta_time_var.set(mc_data["delta_time"])
        else:
            self.delta_time_var.set(0.5)

        # Solo usar los comandos del MC, si no tiene, tabla vacía
        command_configs = mc_data.get("command_configs", {}) if mc_data else {}
        last_state = mc_data.get("last_state", {}) if mc_data else {}

        # Limpiar tabla
        for row_data in self.command_rows:
            row_data["frame"].destroy()
        self.command_rows.clear()

        # Si no hay comandos, no mostrar filas
        if not command_configs:
            return

        # Comandos que necesitan columna de repeticiones
        repeatable_commands = ["X_02_TestTrigger", "X_03_RO_Single"]
        # Comandos que NO tienen botones (automáticos al marcar checkbox)
        auto_commands = ["X_FF_Reset", "X_02_TestTrigger", "X_03_RO_Single"]

        # Recrear filas en el nuevo orden
        for idx, (cmd_name, cmd_config) in enumerate(command_configs.items()):
            if cmd_name not in last_state:
                continue 

            bg_color = "#f7f7f7"
            row_frame = tk.Frame(self.commands_table_frame, relief="ridge", borderwidth=1, bg=bg_color, height=35)
            row_frame.pack(fill="x")
            row_frame.pack_propagate(False)
            row_frame.grid_propagate(False)

            # Configurar el grid para centrar verticalmente
            row_frame.grid_rowconfigure(0, weight=1)

            # Restaurar estado si existe, sino inicializar
            state_val = last_state.get(cmd_name, None)
            enabled_val = bool(state_val)
            
            # Extraer comando base para verificar tipo
            base_cmd = cmd_name.split('#')[0] if '#' in cmd_name else cmd_name

            # Para comandos automáticos, el checkbox debe estar marcado si state_val == "ON"
            if base_cmd in auto_commands:
                enabled_val = (state_val == "ON")
            else:
                enabled_val = bool(state_val)

            self.commands_state[cmd_name] = {
                        "enabled": tk.BooleanVar(value=enabled_val),
                        "state": state_val if state_val else ("ON" if base_cmd in auto_commands else None),
            }
            
            # Si es un comando repetible, restaurar variable de repeticiones
            if base_cmd in repeatable_commands:
                reps_key = f"{cmd_name}_reps"
                saved_reps = last_state.get(reps_key, 1)
                self.commands_state[cmd_name]["repetitions"] = tk.IntVar(value=saved_reps)

            # Checkbox
            checkbox = tk.Checkbutton(
                row_frame, variable=self.commands_state[cmd_name]["enabled"], bg=bg_color
            )
            checkbox.grid(row=0, column=0, padx=5, sticky="")

            # Nombre del comando
            tk.Label(
                row_frame, text=cmd_name, width=54, font=("Arial", 9), bg=bg_color
            ).grid(row=0, column=1, sticky="w")

            col_offset = 2

            # Si es comando repetible, agregar spinbox de repeticiones
            if base_cmd in repeatable_commands:
                tk.Label(row_frame, text="Repetir:", font=("Arial", 8), bg=bg_color).grid(row=0, column=col_offset, padx=(5,2))
                col_offset += 1
                
                repetitions_spinbox = tk.Spinbox(
                    row_frame,
                    from_=1,
                    to=1000,
                    textvariable=self.commands_state[cmd_name]["repetitions"],
                    width=5,
                    justify="center"
                )
                repetitions_spinbox.grid(row=0, column=col_offset, padx=2)
                col_offset += 1
                
            # Solo agregar botones si NO es un comando automático
            if base_cmd not in auto_commands:
                # Obtener llaves para los botones
                btn_keys = list(cmd_config.keys())
                btn1_text = btn_keys[0] if len(btn_keys) > 0 else "ON"
                btn2_text = btn_keys[1] if len(btn_keys) > 1 else "OFF"

                # Botón ON
                on_btn = tk.Button(
                    row_frame,
                    text=btn1_text,
                    width=8,
                    height=1,
                    bg="#e0e0e0",
                    command=lambda cmd=cmd_name, state=btn1_text: self.toggle_command_state(cmd, state),
                )
                on_btn.grid(row=0, column=col_offset, padx=2, pady=2)
                col_offset += 1

                # Guardar referencia del botón ON
                self.commands_state[cmd_name]["on_btn"] = on_btn

                # Botón OFF si tiene dos opciones
                if len(btn_keys) > 1:
                    off_btn = tk.Button(
                        row_frame,
                        text=btn2_text,
                        width=8,
                        height=1,
                        bg="#e0e0e0",
                        command=lambda cmd=cmd_name, state=btn2_text: self.toggle_command_state(cmd, state),
                    )
                    off_btn.grid(row=0, column=col_offset, padx=2, pady=2)
                    self.commands_state[cmd_name]["off_btn"] = off_btn
                    col_offset += 1
                else:
                    self.commands_state[cmd_name]["off_btn"] = None

                # Cargar estado guardado si existe
                if state_val == btn1_text:
                    on_btn.config(bg="#27ae60", relief="sunken")
                    if self.commands_state[cmd_name].get("off_btn"):
                        self.commands_state[cmd_name]["off_btn"].config(bg="#e0e0e0", relief="raised")
                elif state_val == btn2_text:
                    if self.commands_state[cmd_name].get("off_btn"):
                        self.commands_state[cmd_name]["off_btn"].config(bg="#e74c3c", relief="sunken")
                    on_btn.config(bg="#e0e0e0", relief="raised")
                else:
                    on_btn.config(bg="#e0e0e0", relief="raised")
                    if self.commands_state[cmd_name].get("off_btn"):
                        self.commands_state[cmd_name]["off_btn"].config(bg="#e0e0e0", relief="raised")
            else:
                # Para comandos automáticos, no hay botones
                self.commands_state[cmd_name]["on_btn"] = None
                self.commands_state[cmd_name]["off_btn"] = None
                tk.Label(
                    row_frame, 
                    text="", 
                    font=("Arial", 8, "italic"), 
                    fg="gray",
                    bg=bg_color
                ).grid(row=0, column=col_offset, padx=10)

            self.command_rows.append({"frame": row_frame, "cmd_name": cmd_name})
            self.setup_drag_and_drop(row_frame, cmd_name)

        # Vincular scroll a las nuevas filas creadas
        self.root.after(150, self.bind_scroll_to_new_rows)

    def bind_scroll_to_new_rows(self):
        """Vincula eventos de scroll a las filas recién creadas de la tabla de comandos"""
        def bind_mousewheel(widget):
            widget.bind("<MouseWheel>", self.on_commands_mousewheel)
            widget.bind("<Button-4>", self.on_commands_mousewheel)
            widget.bind("<Button-5>", self.on_commands_mousewheel)
        
        def bind_to_children(parent):
            try:
                bind_mousewheel(parent)
                for child in parent.winfo_children():
                    if not isinstance(child, (tk.Spinbox, ttk.Combobox)):
                        bind_to_children(child)
            except Exception:
                pass
        
        # Buscar el canvas padre en la pestaña de comandos
        commands_tab = self.notebook.nametowidget(self.notebook.select())
        for child in commands_tab.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
                break
        else:
            return
        
        # Vincular a todas las filas nuevas
        for row_data in self.command_rows:
            bind_to_children(row_data["frame"])

    def on_commands_mousewheel(self, event):
        """Manejador de scroll específico para la pestaña de comandos"""
        # Buscar el canvas en la pestaña de comandos
        commands_tab = self.notebook.nametowidget(self.notebook.select())
        for child in commands_tab.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
                break
        else:
            return
        
        # Determinar la dirección del scroll
        if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
            canvas.yview_scroll(1, "units")
        elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
            canvas.yview_scroll(-1, "units")
        return "break"

    def init_database(self):
        """Inicializa el almacenamiento y gestión de estados desde db.json"""
        nombre_archivo = db_json

        if os.path.exists(nombre_archivo):
            # El archivo existe: intenta cargarlo
            try:
                with open(nombre_archivo, "r", encoding="utf-8") as f:
                    # Intenta cargar el contenido en self.db
                    self.db = json.load(f)
                    matched_macs = self.db.get("mc_registered")
                    for mac_origin in matched_macs.keys():
                        self.mc_registered[mac_origin] = matched_macs.get(mac_origin)

                print(f"Archivo '{nombre_archivo}' cargado exitosamente.")

            except json.JSONDecodeError:
                # Caso: El archivo existe, pero está vacío o mal formado (corrupto)
                print(
                    f"Advertencia: '{nombre_archivo}' está vacío o corrupto. Inicializando con diccionario vacío."
                )
                self.db = {}

            except Exception as e:
                # Manejo de otros posibles errores de lectura
                print(f"Error al leer '{nombre_archivo}': {e}")
                self.db = {}

        else:
            # El archivo NO existe: créalo e inicializa self.db
            self.db = {}
            try:
                with open(nombre_archivo, "w", encoding="utf-8") as f:
                    # Escribe el diccionario vacío en el nuevo archivo (con formato legible)
                    json.dump(self.db, f, indent=4)
                print(f"Archivo '{nombre_archivo}' creado e inicializado con éxito.")

            except Exception as e:
                print(f"Error al crear '{nombre_archivo}': {e}")

    def create_main_interface(self):
        """Crea la interfaz principal de la aplicación"""
        # Notebook para las pestañas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Pestañas
        self.create_dashboard_tab()
        self.create_commands_tab()

        # Menú
        self.create_menu()

    def create_dashboard_tab(self):
        """Crea la pestaña del dashboard con scroll corregido"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")

        # Canvas con scrollbar para todo el dashboard
        canvas = tk.Canvas(dashboard_frame, borderwidth=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(dashboard_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Función para ajustar el ancho del frame interno cuando el canvas cambie de tamaño
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas_width)

        # Sistema mejorado de scroll con rueda del mouse
        def bind_mousewheel(widget):
            """Vincula eventos de scroll a un widget específico"""
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", on_mousewheel)
            widget.bind("<Button-5>", on_mousewheel)

        def on_mousewheel(event):
            """Maneja todos los eventos de scroll del mouse"""
            # Determinar la dirección del scroll
            if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
                canvas.yview_scroll(1, "units")
            elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
                canvas.yview_scroll(-1, "units")
            return "break"  # Prevenir propagación del evento

        # Vincular scroll al canvas principal
        bind_mousewheel(canvas)
        
        # Vincular scroll al frame desplazable y a todos sus hijos
        def bind_to_all_children(parent):
            """Vincula eventos de scroll recursivamente a todos los widgets hijos"""
            try:
                bind_mousewheel(parent)
                for child in parent.winfo_children():
                    # No vincular a widgets que tienen su propio scroll
                    if not isinstance(child, (scrolledtext.ScrolledText, tk.Listbox, tk.Text)):
                        bind_to_all_children(child)
            except Exception:
                pass  # Ignorar errores en widgets que no soportan binding

        # Vincular después de que la UI esté completamente construida
        def bind_scroll_after_ui():
            bind_to_all_children(scrollable_frame)
            # También vincular el canvas mismo (por si acaso)
            bind_mousewheel(canvas)

        # Programar el binding después de que la UI esté creada
        self.root.after(100, bind_scroll_after_ui)

        ###
        # Frame superior para Gestionar Micro Controladores
        stats_frame = tk.LabelFrame(
            scrollable_frame,  
            text="Panel de gestión de Micro Controladores",
            font=("Arial", 12, "bold"),
        )
        stats_frame.pack(fill="x", padx=10, pady=5)

        # Crear grid para gestor de Micro Controladores
        stats_grid = tk.Frame(stats_frame)
        stats_grid.pack(fill="x", padx=10, pady=10)

        # Tramas enviadas
        tk.Label(
            stats_grid,
            text="Micro Controladores Conectados",
            font=("Arial", 10, "bold"),
        ).grid(row=0, column=0, sticky="w")
        self.frames_sent_label = tk.Label(
            stats_grid, text=f"{len(self.mc_available)}", font=("Arial", 10)
        )
        self.frames_sent_label.grid(row=0, column=1, padx=20)

        # Tabla de micro controladores pareados interfaz-mac
        table_frame = tk.Frame(stats_grid)
        table_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=(10, 0))

        columns = (
            "Interfaz de Red",
            "MAC Origen",
            "MAC Destino",
            "Interfaz Destino",
            "Label",
        )
        self.mc_table = ttk.Treeview(
            table_frame, columns=columns, show="headings", height=5
        )
        for col in columns:
            self.mc_table.heading(col, text=col)
            self.mc_table.column(col, width=150, anchor="center")

        self.mc_table.pack(fill="x", expand=True)

        # Insertar datos iniciales
        for mac_source, interfaz in self.mc_available.items():
            if self.mc_registered.get(f"{mac_source}"):
                mac_destiny = self.mc_registered.get(f"{mac_source}").get("mac_destiny")
                label = self.mc_registered.get(f"{mac_source}").get("label")
                self.mc_table.insert(
                    "", "end", values=(interfaz, mac_source, mac_destiny, label)
                )

        self.mc_table.pack(fill="x", expand=True)

        # Botón para refrescar micro controladores conectados
        refresh_btn = tk.Button(
            stats_grid,
            text="🔄 Refrescar Micro Controladores",
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            command=self.refresh_dashboard_mc_table,
        )
        refresh_btn.grid(row=0, column=2, padx=10)

        self.refresh_dashboard_mc_table()

        # CONTENEDOR PRINCIPAL PARA REGISTRO Y PET SCAN (DIVIDIDO EN 2 COLUMNAS)
        main_container = tk.Frame(scrollable_frame)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # COLUMNA IZQUIERDA: FORMULARIO DE REGISTRO (50%)
        register_frame = tk.LabelFrame(
            main_container,
            text="Registrar Micro Controlador",
            font=("Arial", 12, "bold"),
        )
        register_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        form_container = tk.Frame(register_frame)
        form_container.pack(fill="x", padx=10, pady=10)

        # Fila 1: MAC Origen
        mac_origen_row = tk.Frame(form_container)
        mac_origen_row.pack(fill="x", pady=5)

        tk.Label(
            mac_origen_row,
            text="MAC Origen:",
            font=("Arial", 10, "bold"),
            width=15,
            anchor="w",
        ).pack(side="left")

        self.mac_origen_var = tk.StringVar()
        self.mac_origen_combo = ttk.Combobox(
            mac_origen_row,
            textvariable=self.mac_origen_var,
            values=list(self.mc_available.keys()),
            state="readonly",
            width=30,
        )
        self.mac_origen_combo.pack(side="left", padx=(10, 0))
        self.mac_origen_combo.set("Seleccione MAC origen...")

        # Fila 2: MAC Destino
        mac_destino_row = tk.Frame(form_container)
        mac_destino_row.pack(fill="x", pady=5)

        tk.Label(
            mac_destino_row,
            text="MAC Destino:",
            font=("Arial", 10, "bold"),
            width=15,
            anchor="w",
        ).pack(side="left")

        self.mac_destino_var = tk.StringVar()
        self.mac_destino_entry = tk.Entry(
            mac_destino_row, textvariable=self.mac_destino_var, width=32
        )
        self.mac_destino_entry.pack(side="left", padx=(10, 5))

        tk.Label(
            mac_destino_row,
            text="(ej: fe:80:ab:cd:12:34)",
            fg="gray",
            font=("Arial", 8),
        ).pack(side="left")

        # Fila 3: Interfaz Destino
        interface_destino_row = tk.Frame(form_container)
        interface_destino_row.pack(fill="x", pady=5)

        tk.Label(
            interface_destino_row,
            text="Interfaz Destino:",
            font=("Arial", 10, "bold"),
            width=15,
            anchor="w",
        ).pack(side="left")

        self.interface_destino_var = tk.StringVar()
        interface_destino_entry = tk.Entry(
            interface_destino_row, textvariable=self.interface_destino_var, width=32
        )
        interface_destino_entry.pack(side="left", padx=(10, 5))

        tk.Label(
            interface_destino_row,
            text="(ej: eth0, enp3s0)",
            fg="gray",
            font=("Arial", 8),
        ).pack(side="left")

        # Fila 4: Label
        label_row = tk.Frame(form_container)
        label_row.pack(fill="x", pady=5)

        tk.Label(
            label_row,
            text="Etiqueta:",
            font=("Arial", 10, "bold"),
            width=15,
            anchor="w",
        ).pack(side="left")

        self.label_var = tk.StringVar()
        label_entry = tk.Entry(label_row, textvariable=self.label_var, width=32)
        label_entry.pack(side="left", padx=(10, 5))

        tk.Label(label_row, text="(opcional)", fg="gray", font=("Arial", 8)).pack(
            side="left"
        )

        # Botón enviar
        button_row = tk.Frame(form_container)
        button_row.pack(fill="x", pady=10)

        register_btn = tk.Button(
            button_row,
            text="Registrar Micro Controlador",
            command=self.register_mc,
            font=("Arial", 10, "bold"),
            bg="#27ae60",
            fg="white",
            width=25,
            height=1,
        )
        register_btn.pack()

        # COLUMNA DERECHA: PET SCAN (50%)
        pet_scan_frame = tk.LabelFrame(
            main_container,
            text="Pet Scan",
            font=("Arial", 12, "bold"),
        )
        pet_scan_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

                # Canvas para dibujar el círculo de PETs
        pet_canvas = tk.Canvas(pet_scan_frame, width=450, height=450, bg="white")
        pet_canvas.pack(padx=20, pady=20)

        # Checkbox "Seleccionar todos" arriba del canvas
        select_all_pets_frame = tk.Frame(pet_scan_frame, bg="#f7f7f7")
        select_all_pets_frame.pack(before=pet_canvas, pady=(10, 5))
        
        self.select_all_pets_var = tk.BooleanVar(value=False)
        
        def toggle_all_pets():
            """Marca/desmarca todos los checkboxes de PETs"""
            value = self.select_all_pets_var.get()
            for i in range(1, 11):
                self.pet_associations[i]["enabled"] = value
            # Actualizar todas las variables de los checkboxes
            if hasattr(self, 'pet_checkbox_vars'):
                for var in self.pet_checkbox_vars.values():
                    var.set(value)
        
        select_all_pets_cb = tk.Checkbutton(
            select_all_pets_frame,
            text="Seleccionar todos",
            variable=self.select_all_pets_var,
            command=toggle_all_pets,
            font=("Arial", 10, "bold"),
            bg="#f7f7f7"
        )
        select_all_pets_cb.pack()

        # Dibujar 10 rectángulos en círculo        
        center_x = 225  
        center_y = 225  
        radius = 150    
        num_pets = 10

        self.pet_buttons = []
        self.pet_tooltips = []  # Lista para mantener referencias a tooltips
        self.pet_checkbox_vars = {}  # Diccionario para mantener referencias a las variables

        for i in range(num_pets):
            angle = (2 * math.pi / num_pets) * i - (math.pi / 2) 
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            # Calcular posición del checkbox (arriba y más cerca del botón)
            checkbox_offset = 30
            cb_x = x
            cb_y = y - checkbox_offset

                        # Crear variable BooleanVar vinculada al estado en pet_associations
            pet_enabled_var = tk.BooleanVar(value=self.pet_associations[i+1]["enabled"])
            self.pet_checkbox_vars[i+1] = pet_enabled_var  # Guardar referencia
            
            # Función para actualizar el estado cuando cambie el checkbox
            def update_pet_enabled(pet_num, var):
                self.pet_associations[pet_num]["enabled"] = var.get()
                # Actualizar el checkbox "Seleccionar todos" si es necesario
                all_selected = all(self.pet_associations[j]["enabled"] for j in range(1, 11))
                self.select_all_pets_var.set(all_selected)
            
            # Crear checkbox
            pet_checkbox = tk.Checkbutton(
                pet_canvas,
                variable=pet_enabled_var,
                bg="white",
                activebackground="white",
                command=lambda num=i+1, v=pet_enabled_var: update_pet_enabled(num, v)
            )
            pet_canvas.create_window(cb_x, cb_y, window=pet_checkbox)

            # Crear botón con bordes redondeados
            pet_btn = tk.Button(
                pet_canvas,
                text=f"PET {i+1}",
                font=("Arial", 9, "bold"),
                bg="#3498db",
                fg="white",
                width=8,
                height=2,
                relief="flat",          
                borderwidth=0,          
                highlightthickness=2,   
                highlightbackground="#2980b9",  
                cursor="hand2",        
                command=lambda pet_num=i+1: self.on_pet_click(pet_num)
            )
            
            # Colocar el botón en el canvas
            pet_canvas.create_window(x, y, window=pet_btn)
            self.pet_buttons.append(pet_btn)
            
            # Configurar tooltip para este botón
            self.setup_pet_tooltip(pet_btn, i+1)

        # Botón "Enviar" en el centro del círculo
        send_pet_btn = tk.Button(
            pet_canvas,
            text="Enviar",
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            width=10,
            height=2,
            relief="raised",
            borderwidth=3,
            cursor="hand2",
            command=lambda: self.add_response("🚀 Botón Enviar PET presionado (funcionalidad pendiente)")
        )
        
        # Colocar el botón en el centro del círculo
        pet_canvas.create_window(center_x, center_y, window=send_pet_btn)

        # Área de respuestas/log
        response_frame = tk.LabelFrame(
            scrollable_frame,
            text="Respuestas / Log", 
            font=("Arial", 10, "bold")
        )
        response_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.response_text = scrolledtext.ScrolledText(
            response_frame, height=8, font=("Consolas", 10)
        )
        self.response_text.pack(fill="both", expand=True)
        
    def setup_pet_tooltip(self, button, pet_num):
        """Configura el tooltip hover para un botón PET"""
        tooltip = None
        
        def show_tooltip(event):
            nonlocal tooltip
            
            # Obtener información de asociación
            assoc = self.pet_associations[pet_num]
            mc_label = "Sin MC"
            
            if assoc["mc"]:
                # Buscar el label del MC
                for mc_data in self.mc_registered.values():
                    if mc_data.get("mac_destiny") == assoc["mc"]:
                        mc_label = mc_data.get("label", "Sin etiqueta")
                        break
            
            # Crear tooltip
            x = button.winfo_rootx() + button.winfo_width() // 2
            y = button.winfo_rooty() - 10
            
            tooltip = tk.Toplevel(button)
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{x}+{y}")
            
            # Frame contenedor con borde
            frame = tk.Frame(
                tooltip,
                background="#2c3e50",
                relief="solid",
                borderwidth=1
            )
            frame.pack(fill="both", expand=True)
            
            # Contenido del tooltip
            tk.Label(
                frame,
                text=f"PET {pet_num}",
                font=("Arial", 9, "bold"),
                bg="#2c3e50",
                fg="white",
                padx=10,
                pady=2
            ).pack()
            
            tk.Label(
                frame,
                text=f"MC: {mc_label}",
                font=("Arial", 8),
                bg="#2c3e50",
                fg="#ecf0f1",
                padx=10,
                pady=2
            ).pack()
            
            # Ajustar posición para que aparezca arriba del botón
            tooltip.update_idletasks()
            tooltip_height = tooltip.winfo_height()
            tooltip.wm_geometry(f"+{x - tooltip.winfo_width()//2}+{y - tooltip_height - 5}")
        
        def hide_tooltip(event=None):
            nonlocal tooltip
            if tooltip:
                tooltip.destroy()
                tooltip = None
        
        # Handler para el clic que oculta el tooltip antes de abrir el modal
        def on_click(event):
            hide_tooltip()
            # Dar un pequeño delay para que el tooltip se destruya antes del modal
            button.after(10, lambda: button.invoke())
            return "break"  # Prevenir propagación
        
        button.bind("<Enter>", show_tooltip)
        button.bind("<Leave>", hide_tooltip)
        button.bind("<Button-1>", on_click)

    def on_pet_click(self, pet_num):
        """Maneja el clic en un botón PET - abre modal de configuración"""
        # Crear modal pero no hacer grab_set inmediatamente
        modal = tk.Toplevel(self.root)
        modal.title(f"Configurar PET {pet_num}")
        modal.transient(self.root)
        modal.resizable(False, False)
        modal.configure(bg="#f7f7f7")
        
        # Esperar a que el modal sea visible antes de hacer grab
        modal.update_idletasks()
        modal.after(50, lambda: modal.grab_set())
        
        self.center_modal_on_parent(modal, 500, 400)
        
        # Título
        tk.Label(
            modal,
            text=f"Configurar PET {pet_num}",
            font=("Arial", 14, "bold"),
            bg="#f7f7f7"
        ).pack(pady=(20, 10))
        
        # Obtener asociación actual
        current_assoc = self.pet_associations[pet_num]
        
        # Frame principal de contenido
        content_frame = tk.Frame(modal, bg="#f7f7f7")
        content_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        # Sección Micro Controlador
        mc_section = tk.LabelFrame(
            content_frame,
            text="Micro Controlador",
            font=("Arial", 11, "bold"),
            bg="#f7f7f7"
        )
        mc_section.pack(fill="x", pady=(0, 15))
        
        mc_frame = tk.Frame(mc_section, bg="#f7f7f7")
        mc_frame.pack(fill="x", padx=15, pady=10)
        
        tk.Label(
            mc_frame,
            text="Seleccionar MC:",
            font=("Arial", 10),
            bg="#f7f7f7"
        ).pack(anchor="w", pady=(0, 5))
        
        mc_var = tk.StringVar()
        mc_options = ["Sin MC"] + self.get_mc_display_list()
        
        # Establecer valor inicial
        if current_assoc["mc"]:
            for option in mc_options:
                if " | " in option and option.split(" | ")[1] == current_assoc["mc"]:
                    mc_var.set(option)
                    break
        else:
            mc_var.set("Sin MC")
        
        mc_combo = ttk.Combobox(
            mc_frame,
            textvariable=mc_var,
            values=mc_options,
            state="readonly",
            width=40
        )
        mc_combo.pack(fill="x")
        
        # Frame de botones
        btn_frame = tk.Frame(modal, bg="#f7f7f7")
        btn_frame.pack(fill="x", pady=(10, 20))
        
        def guardar():
            selected_mc_display = mc_var.get()
            
            # Actualizar asociación (mantener enabled)
            if selected_mc_display == "Sin MC":
                self.pet_associations[pet_num]["mc"] = None
            else:
                selected_mc = self.get_mac_from_selection(selected_mc_display)
                self.pet_associations[pet_num]["mc"] = selected_mc

            # TODO: Guardar en db cuando esté definido el formato
            # self.save_pet_associations_to_db()
            
            self.add_response(f"✓ PET {pet_num} configurado correctamente")
            modal.destroy()
        
        guardar_btn = tk.Button(
            btn_frame,
            text="Guardar",
            font=("Arial", 10, "bold"),
            bg="#27ae60",
            fg="white",
            command=guardar,
            width=10
        )
        guardar_btn.pack(side="left", padx=(80, 10))
        
        cancelar_btn = tk.Button(
            btn_frame,
            text="Cancelar",
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            command=modal.destroy,
            width=10
        )
        cancelar_btn.pack(side="right", padx=(10, 80))


    def create_commands_tab(self):
        """Crea la pestaña de comandos con scroll corregido"""
        # Frame principal de la pestaña
        commands_tab = ttk.Frame(self.notebook)
        self.notebook.add(commands_tab, text="Comandos")

        # Detecta y carga las interfaces ethernet
        self.refresh_mc_list()

        # Canvas con scrollbar
        canvas = tk.Canvas(commands_tab, borderwidth=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(commands_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window(
            (0, 0), window=scrollable_frame, anchor="nw"
        )
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Función para ajustar el ancho del frame interno cuando el canvas cambie de tamaño
        def configure_canvas_width(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind("<Configure>", configure_canvas_width)

        # Sistema mejorado de scroll con rueda del mouse
        def bind_mousewheel(widget):
            """Vincula eventos de scroll a un widget específico"""
            widget.bind("<MouseWheel>", on_mousewheel)
            widget.bind("<Button-4>", on_mousewheel)
            widget.bind("<Button-5>", on_mousewheel)

        def on_mousewheel(event):
            """Maneja todos los eventos de scroll del mouse"""
            # Determinar la dirección del scroll
            if event.num == 5 or (hasattr(event, "delta") and event.delta < 0):
                canvas.yview_scroll(1, "units")
            elif event.num == 4 or (hasattr(event, "delta") and event.delta > 0):
                canvas.yview_scroll(-1, "units")
            return "break"  # Prevenir propagación del evento

        # Vincular scroll al canvas principal
        bind_mousewheel(canvas)
        
        # Vincular scroll al frame desplazable y a todos sus hijos
        def bind_to_all_children(parent):
            """Vincula eventos de scroll recursivamente a todos los widgets hijos"""
            try:
                bind_mousewheel(parent)
                for child in parent.winfo_children():
                    # No vincular a widgets que tienen su propio scroll
                    if not isinstance(child, (scrolledtext.ScrolledText, tk.Listbox, tk.Text, ttk.Combobox, tk.Spinbox)):
                        bind_to_all_children(child)
            except Exception:
                pass  # Ignorar errores en widgets que no soportan binding

        # Vincular después de que la UI esté completamente construida
        def bind_scroll_after_ui():
            bind_to_all_children(scrollable_frame)
            # También vincular el canvas mismo
            bind_mousewheel(canvas)

        # Programar el binding después de que la UI esté creada
        self.root.after(100, bind_scroll_after_ui)

        # Select MC Destino (arriba de ambos frames)
        mc_select_frame = tk.Frame(scrollable_frame)
        mc_select_frame.pack(fill="x", padx=10, pady=(5, 0))

        tk.Label(
            mc_select_frame,
            text="Micro Controlador Destino:",
            font=("Arial", 10, "bold"),
            anchor="w",
        ).pack(side="left", padx=(0, 10))

        self.mc_var = tk.StringVar()
        self.mc_combo = ttk.Combobox(
            mc_select_frame,
            textvariable=self.mc_var,
            values=self.get_mc_display_list(),
            state="readonly",
            width=40,
        )
        self.mc_combo.pack(side="left")
        self.mc_combo.set("Seleccione MC...")
        self.mc_combo.bind("<<ComboboxSelected>>", lambda e: self.rebuild_command_table())

        # Contenedor principal para la zona de formularios y la tabla de comandos
        main_row_container = tk.Frame(scrollable_frame)
        main_row_container.pack(fill="both", expand=True, padx=10, pady=5)

        # Frame derecho: Comandos
        controls_frame = tk.LabelFrame(main_row_container, text="Comandos")
        controls_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        # Container principal de la tabla y controles
        commands_main_container = tk.Frame(controls_frame)
        commands_main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Delta Tiempo Comandos
        delta_time_frame = tk.Frame(commands_main_container)
        delta_time_frame.pack(fill="x", pady=(0, 10))

        tk.Label(
            delta_time_frame,
            text="Delta Tiempo Comandos (seg):",
            font=("Arial", 9, "bold"),
        ).pack(side="left")

        self.delta_time_var = tk.DoubleVar(value=0.5)
        delta_time_spinbox = tk.Spinbox(
            delta_time_frame,
            from_=0.1,
            to=10.0,
            increment=0.1,
            textvariable=self.delta_time_var,
            width=8,
            justify="center",
            format="%.1f",
        )
        delta_time_spinbox.pack(side="left", padx=(5, 0))

        # Botones de Macros
        macros_frame = tk.Frame(delta_time_frame)
        macros_frame.pack(side="right", padx=(10, 0))
        
        save_macro_btn = tk.Button(
            macros_frame,
            text="💾 Guardar Macro",
            font=("Arial", 9, "bold"),
            bg="#27ae60",
            fg="white",
            command=self.save_macro
        )
        save_macro_btn.pack(side="left", padx=(0, 5))
        
        load_macro_btn = tk.Button(
            macros_frame,
            text="📂 Cargar Macro",
            font=("Arial", 9, "bold"),
            bg="#3498db",
            fg="white",
            command=self.load_macro
        )
        load_macro_btn.pack(side="left", padx=(0, 5))

        # Botón "Gestionar Comandos"
        add_command_btn = tk.Button(
            delta_time_frame,
            text="Gestionar Comandos",
            font=("Arial", 9, "bold"),
            bg="#f1c40f",
            command=self.open_add_command_modal
        )
        add_command_btn.pack(side="right", padx=(10, 0))

        # Tabla de comandos
        table_frame = tk.Frame(commands_main_container)
        table_frame.pack(fill="both", expand=True)

        # Headers
        header_frame = tk.Frame(table_frame, relief="ridge", borderwidth=1)
        header_frame.pack(fill="x")

        # Checkbox "Seleccionar todo"
        def toggle_all_commands():
            value = select_all_cb_var.get()
            for cmd_state in self.commands_state.values():
                cmd_state["enabled"].set(value)

        select_all_cb_var = tk.BooleanVar(value=False)
        select_all_cb = tk.Checkbutton(
            header_frame,
            variable=select_all_cb_var,
            command=toggle_all_commands,
            width=2
        )
        select_all_cb.grid(row=0, column=0, padx=1, pady=2)

        tk.Label(
            header_frame, text="Comando", width=58, font=("Arial", 8, "bold")
        ).grid(row=0, column=1)
        tk.Label(
            header_frame, text="ON/HIGH/GLOBAL", width=15, font=("Arial", 8, "bold"), padx=10
        ).grid(row=0, column=2)
        tk.Label(header_frame, text="OFF/LOW/LOCAL", width=16, font=("Arial", 8, "bold")).grid(
            row=0, column=3
        )

        # Definir comandos con sus appendix
        self.command_configs = {
            "X_02_TestTrigger": {"ON": "X_02_TestTrigger"},  
            "X_03_RO_Single": {"ON": "X_03_RO_Single"},
            "X_04_RO_ON | X_05_RO_OFF": {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"},
            "X_08_DIAG_ | X_09_DIAG_DIS": {"ON": "X_08_DIAG_", "OFF": "X_09_DIAG_DIS"},
            "X_FB_TTrig_Auto_EN | X_FC_TTrig_Auto_DIS": {
                "ON": "X_FB_TTrig_Auto_EN",
                "OFF": "X_FC_TTrig_Auto_DIS",
            },
            "X_FF_Reset": {"ON": "X_FF_Reset"},
            "X_20_PwrDwnb_TOP_ON | X_21_PwrDwnb_TOP_OFF": {"ON": "X_20_PwrDwnb_TOP_ON", "OFF": "X_21_PwrDwnb_TOP_OFF"},
            "X_22_PwrDwnb_BOT_ON | X_23_PwrDwnb_BOT_OFF": {
                "ON": "X_22_PwrDwnb_BOT_ON",
                "OFF": "X_23_PwrDwnb_BOT_OFF",
            },
            "X_26_PwrEN_2V4D_ON | X_27_PwrEN_2V4D_OFF": {"ON": "X_26_PwrEN_2V4D_ON", "OFF": "X_27_PwrEN_2V4D_OFF"},
            "X_28_PwrEN_3V1_ON | X_29_PwrEN_3V1_OFF": {"ON": "X_28_PwrEN_3V1_ON", "OFF": "X_29_PwrEN_3V1_OFF"},
            "X_2A_PwrEN_1V8A_ON | X_2B_PwrEN_1V8A_OFF": {"ON": "X_2A_PwrEN_1V8A_ON", "OFF": "X_2B_PwrEN_1V8A_OFF"},
            "X_E1_FanSpeed0_High | X_E0_FanSpeed0_Low": {
            "HIGH": "X_E1_FanSpeed0_High", "LOW": "X_E0_FanSpeed0_Low"
            },
            "X_F9_TTrig_Global | X_FA_TTrig_Local": {"GLOBAL": "X_F9_TTrig_Global", "LOCAL": "X_FA_TTrig_Local"},
            "X_E3_FanSpeed1_High | X_E2_FanSpeed1_Low": {"HIGH": "X_E3_FanSpeed1_High", "LOW": "X_E2_FanSpeed1_Low"},
        }

        # Estado de comandos: {comando: {"enabled": bool, "state": "ON"/"OFF"/None}}
        self.commands_state = {}

        # Crear filas para cada comando
        # Inicializar lista para tracking de filas
        self.command_rows = []

        # Guardar referencia al frame contenedor
        self.commands_table_frame = table_frame

        self.show_summary_var = tk.BooleanVar(value=False)
        summary_frame = tk.Frame(commands_main_container)
        summary_frame.pack(fill="x", pady=(10, 0))

        summary_checkbox = tk.Checkbutton(
            summary_frame,
            text="Ventana Resumen",
            variable=self.show_summary_var,
            font=("Arial", 9),
        )
        summary_checkbox.pack(side="left", padx=(0, 10))

        # Botón enviar comandos
        self.send_commands_btn = tk.Button(
            commands_main_container,
            text="Enviar Comandos",
            command=self.toggle_send_commands, 
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            width=25,
            height=2,
            relief="raised",
        )
        self.send_commands_btn.pack(pady=(10, 0))
        
    def toggle_send_commands(self):
        """Alterna entre enviar y cancelar comandos"""
        if self.sending_commands:
            # Si está enviando, cancelar
            self.cancel_sending = True
            self.add_response("⚠️ Cancelación solicitada...")
        else:
            # Si no está enviando, iniciar envío
            self.send_selected_commands()

    def save_macro(self):
        """Guarda la configuración actual de comandos como una macro"""
        selected_mc_display = self.mc_var.get()
        selected_mc = self.get_mac_from_selection(selected_mc_display)
        if not selected_mc:
            messagebox.showwarning("Validación", "Debe seleccionar un Micro Controlador.")
            return

        # Buscar el MC seleccionado
        mc_data = None
        for data in self.mc_registered.values():
            if data.get("mac_destiny") == selected_mc:
                mc_data = data
                break
        
        if not mc_data:
            messagebox.showwarning("Validación", "Micro Controlador no encontrado.")
            return

        # Verificar que hay comandos configurados
        command_configs = mc_data.get("command_configs", {})
        if not command_configs:
            messagebox.showwarning("Validación", "No hay comandos configurados para guardar.")
            return
        
        # Obtener macros existentes
        existing_macros = mc_data.get("macros", {})

        # Calcular altura del modal según cantidad de macros
        base_height = 250  # Altura base (título, input, botones)
        if existing_macros:
            macros_section_height = min(250, len(existing_macros) * 35 + 60)  # Max 250px para el listado
        else:
            macros_section_height = 0
        
        modal_height = base_height + macros_section_height
        
        # Modal para solicitar nombre de la macro
        modal = tk.Toplevel(self.root)
        modal.title("Guardar Macro")
        modal.transient(self.root)
        modal.grab_set()
        modal.resizable(False, False)
        modal.configure(bg="#f7f7f7")

        # Usar el método helper para centrar
        self.center_modal_on_parent(modal, 500, modal_height)  # <-- CAMBIO AQUÍ
        
        tk.Label(
        modal,
        text="Guardar Macro",
        font=("Arial", 12, "bold"),
        bg="#f7f7f7"
        ).pack(pady=(20, 10))

        # Frame para el input del nombre
        name_frame = tk.Frame(modal, bg="#f7f7f7")
        name_frame.pack(fill="x", padx=20, pady=(0, 10))

        tk.Label(
            name_frame,
            text="Nombre de la macro:",
            font=("Arial", 10),
            bg="#f7f7f7"
        ).pack(anchor="w")

        name_var = tk.StringVar()
        name_entry = tk.Entry(name_frame, textvariable=name_var, font=("Arial", 10))
        name_entry.pack(fill="x", pady=(5, 0))
        name_entry.focus()

        # Sección de macros existentes (si hay)
        if existing_macros:
            tk.Label(
                modal,
                text="Macros guardadas (clic para seleccionar):",
                font=("Arial", 10, "bold"),
                bg="#f7f7f7"
            ).pack(anchor="w", padx=20, pady=(10, 5))

            # Frame con scroll para las macros - altura dinámica según cantidad
            max_height = min(250, len(existing_macros) * 35 + 10)  # Máximo 250px
            macros_canvas_frame = tk.Frame(modal, bg="#f7f7f7", height=max_height)
            macros_canvas_frame.pack(fill="x", padx=20, pady=(0, 10))  # <-- CAMBIAR fill="both" a fill="x"
            macros_canvas_frame.pack_propagate(False)

            macros_canvas = tk.Canvas(
                macros_canvas_frame,
                bg="#f7f7f7",
                highlightthickness=1,
                highlightbackground="#ccc"
            )
            macros_scrollbar = tk.Scrollbar(macros_canvas_frame, orient="vertical", command=macros_canvas.yview)
            macros_list_frame = tk.Frame(macros_canvas, bg="#f7f7f7")

            macros_list_frame.bind("<Configure>", lambda e: macros_canvas.configure(scrollregion=macros_canvas.bbox("all")))
            canvas_window = macros_canvas.create_window((0, 0), window=macros_list_frame, anchor="nw")
            
            # Ajustar ancho del frame interno al canvas
            def on_canvas_configure(event):
                macros_canvas.itemconfig(canvas_window, width=event.width)
            
            macros_canvas.bind("<Configure>", on_canvas_configure)
            macros_canvas.configure(yscrollcommand=macros_scrollbar.set)

            macros_canvas.pack(side="left", fill="both", expand=True)
            macros_scrollbar.pack(side="right", fill="y")

            # Agregar cada macro con botón de eliminar
            for macro_name in existing_macros.keys():
                macro_row = tk.Frame(macros_list_frame, bg="white", relief="ridge", borderwidth=1)
                macro_row.pack(fill="x", pady=2, padx=2)

                # Frame para el texto (se expande)
                text_frame = tk.Frame(macro_row, bg="white")
                text_frame.pack(side="left", fill="both", expand=True, padx=5, pady=2)

                # Label con el nombre de la macro (truncado)
                macro_label = tk.Label(
                    text_frame,
                    text=macro_name if len(macro_name) <= 30 else macro_name[:27] + "...",
                    font=("Arial", 9),
                    bg="white",
                    anchor="w",
                    cursor="hand2"
                )
                macro_label.pack(fill="x", expand=True)

                # Tooltip para mostrar nombre completo al hacer hover
                def create_tooltip(widget, text):
                    tooltip = None
                    
                    def on_enter(event):
                        nonlocal tooltip
                        if len(text) > 30:  # Solo mostrar si está truncado
                            x, y, _, _ = widget.bbox("insert")
                            x += widget.winfo_rootx() + 25
                            y += widget.winfo_rooty() + 25
                            
                            tooltip = tk.Toplevel(widget)
                            tooltip.wm_overrideredirect(True)
                            tooltip.wm_geometry(f"+{x}+{y}")
                            
                            label = tk.Label(
                                tooltip,
                                text=text,
                                background="lightyellow",
                                relief="solid",
                                borderwidth=1,
                                font=("Arial", 9)
                            )
                            label.pack()
                    
                    def on_leave(event):
                        nonlocal tooltip
                        if tooltip:
                            tooltip.destroy()
                            tooltip = None
                    
                    widget.bind("<Enter>", on_enter)
                    widget.bind("<Leave>", on_leave)
                
                create_tooltip(macro_label, macro_name)

                # Click para seleccionar
                def select_macro(name):
                    name_var.set(name)
                
                macro_label.bind("<Button-1>", lambda e, name=macro_name: select_macro(name))

                # Botón eliminar (alineado a la derecha)
                def on_delete():
                    if self.delete_macro(mc_data, macro_name, lambda: [modal.destroy(), self.save_macro()]):
                        pass 

                delete_btn = tk.Button(
                    macro_row,
                    text="🗑️",
                    font=("Arial", 10),
                    bg="#e74c3c",
                    fg="white",
                    width=3,
                    command=on_delete
                )
                delete_btn.pack(side="right", padx=5, pady=2)


        # Frame para botones
        btn_frame = tk.Frame(modal, bg="#f7f7f7")
        btn_frame.pack(fill="x", pady=(10, 20), side="bottom")  


        def guardar():
            macro_name = name_var.get().strip()
            if not macro_name:
                messagebox.showwarning("Validación", "Debe ingresar un nombre para la macro.")
                return

            # Verificar si ya existe
            if macro_name in existing_macros:
                if not messagebox.askyesno("Confirmar sobrescritura", f"La macro '{macro_name}' ya existe.\n¿Desea sobrescribirla?"):
                    return

            # Construir last_state actual
            current_last_state = {}
            for cmd_name in command_configs.keys():
                cmd_state = self.commands_state.get(cmd_name, {})
                current_last_state[cmd_name] = cmd_state.get("state", "")
                
                # Guardar repeticiones si aplica
                base_cmd = cmd_name.split('#')[0] if '#' in cmd_name else cmd_name
                if base_cmd in ["X_02_TestTrigger", "X_03_RO_Single"] and "repetitions" in cmd_state:
                    current_last_state[f"{cmd_name}_reps"] = cmd_state["repetitions"].get()

            # Construir datos de la macro
            macro_data = {
                "command_configs": dict(command_configs),
                "last_state": current_last_state,
                "delta_time": self.delta_time_var.get()
            }

            # Guardar en el MC
            if "macros" not in mc_data:
                mc_data["macros"] = {}
            
            mc_data["macros"][macro_name] = macro_data
            self.update_db_stats()
            
            messagebox.showinfo("Éxito", f"Macro '{macro_name}' guardada correctamente.")
            modal.destroy()

        guardar_btn = tk.Button(
            btn_frame,
            text="Guardar",
            font=("Arial", 10, "bold"),
            bg="#27ae60",
            fg="white",
            command=guardar,
            width=10
        )
        guardar_btn.pack(side="left", padx=(40, 10))

        cancelar_btn = tk.Button(
            btn_frame,
            text="Cancelar",
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            command=modal.destroy,
            width=10
        )
        cancelar_btn.pack(side="right", padx=(10, 40))

    def load_macro(self):
        """Carga una macro previamente guardada"""
        selected_mc_display = self.mc_var.get()
        selected_mc = self.get_mac_from_selection(selected_mc_display)
        if not selected_mc:
            messagebox.showwarning("Validación", "Debe seleccionar un Micro Controlador.")
            return

        # Buscar el MC seleccionado
        mc_data = None
        for data in self.mc_registered.values():
            if data.get("mac_destiny") == selected_mc:
                mc_data = data
                break

        if not mc_data:
            messagebox.showwarning("Validación", "Micro Controlador no encontrado.")
            return

        macros = mc_data.get("macros", {})
        if not macros:
            messagebox.showinfo("Información", "No hay macros guardadas para este Micro Controlador.")
            return

        # Modal para seleccionar macro
        modal = tk.Toplevel(self.root)
        modal.title("Cargar Macro")
        modal.transient(self.root)
        modal.grab_set()
        modal.resizable(False, False)
        modal.configure(bg="#f7f7f7")

        # Usar el método helper para centrar
        self.center_modal_on_parent(modal, 500, 400)  # <-- CAMBIO AQUÍ
        
        tk.Label(
            modal,
            text="Seleccione una macro para cargar:",
            font=("Arial", 11, "bold"),
            bg="#f7f7f7"
        ).pack(pady=(20, 10))

        # Frame con scroll para las macros
        macros_canvas_frame = tk.Frame(modal, bg="#f7f7f7")
        macros_canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)

        macros_canvas = tk.Canvas(
            macros_canvas_frame,
            bg="#f7f7f7",
            highlightthickness=1,
            highlightbackground="#ccc"
        )
        macros_scrollbar = tk.Scrollbar(macros_canvas_frame, orient="vertical", command=macros_canvas.yview)
        macros_list_frame = tk.Frame(macros_canvas, bg="#f7f7f7")

        macros_list_frame.bind("<Configure>", lambda e: macros_canvas.configure(scrollregion=macros_canvas.bbox("all")))
        canvas_window = macros_canvas.create_window((0, 0), window=macros_list_frame, anchor="nw")
        
        # Ajustar ancho del frame interno al canvas
        def on_canvas_configure(event):
            macros_canvas.itemconfig(canvas_window, width=event.width)
        
        macros_canvas.bind("<Configure>", on_canvas_configure)
        macros_canvas.configure(yscrollcommand=macros_scrollbar.set)

        macros_canvas.pack(side="left", fill="both", expand=True)
        macros_scrollbar.pack(side="right", fill="y")

        # Variable para almacenar la macro seleccionada
        selected_macro = tk.StringVar()

        # Lista para mantener referencias de todas las filas
        macro_rows_widgets = []

        # Agregar cada macro con botón de eliminar
        for macro_name in macros.keys():
            macro_row = tk.Frame(macros_list_frame, bg="white", relief="ridge", borderwidth=1)
            macro_row.pack(fill="x", pady=2, padx=2)

            # Frame para el texto (se expande)
            text_frame = tk.Frame(macro_row, bg="white")
            text_frame.pack(side="left", fill="both", expand=True, padx=5, pady=2)

            # Label con el nombre de la macro (truncado)
            macro_label = tk.Label(
                text_frame,
                text=macro_name if len(macro_name) <= 30 else macro_name[:27] + "...",
                font=("Arial", 9),
                bg="white",
                anchor="w",
                cursor="hand2"
            )
            macro_label.pack(fill="x", expand=True)

            # Guardar referencias de widgets de esta fila
            macro_rows_widgets.append({
                "row": macro_row,
                "frame": text_frame,
                "label": macro_label
            })

            # Tooltip para mostrar nombre completo al hacer hover
            def create_tooltip(widget, text):
                tooltip = None
                
                def on_enter(event):
                    nonlocal tooltip
                    if len(text) > 30:
                        x, y, _, _ = widget.bbox("insert")
                        x += widget.winfo_rootx() + 25
                        y += widget.winfo_rooty() + 25
                        
                        tooltip = tk.Toplevel(widget)
                        tooltip.wm_overrideredirect(True)
                        tooltip.wm_geometry(f"+{x}+{y}")
                        
                        label = tk.Label(
                            tooltip,
                            text=text,
                            background="lightyellow",
                            relief="solid",
                            borderwidth=1,
                            font=("Arial", 9)
                        )
                        label.pack()
                
                def on_leave(event):
                    nonlocal tooltip
                    if tooltip:
                        tooltip.destroy()
                        tooltip = None
                
                widget.bind("<Enter>", on_enter)
                widget.bind("<Leave>", on_leave)
            
            create_tooltip(macro_label, macro_name)

            # Click para seleccionar
            def select_macro_fn(name, current_row, current_frame, current_label):
                selected_macro.set(name)
                
                # Restaurar color de TODAS las filas
                for widgets in macro_rows_widgets:
                    widgets["row"].config(bg="white")
                    widgets["frame"].config(bg="white")
                    widgets["label"].config(bg="white")
                
                # Aplicar color de selección a la fila actual
                current_row.config(bg="#e3f2fd")
                current_frame.config(bg="#e3f2fd")
                current_label.config(bg="#e3f2fd")
            
            # Bind con argumentos correctos usando valores actuales del loop
            macro_label.bind("<Button-1>", lambda e, n=macro_name, r=macro_row, f=text_frame, l=macro_label: select_macro_fn(n, r, f, l))
            text_frame.bind("<Button-1>", lambda e, n=macro_name, r=macro_row, f=text_frame, l=macro_label: select_macro_fn(n, r, f, l))
            macro_row.bind("<Button-1>", lambda e, n=macro_name, r=macro_row, f=text_frame, l=macro_label: select_macro_fn(n, r, f, l))

            # Botón eliminar
            def on_delete(name):
                if self.delete_macro(mc_data, name, lambda: [modal.destroy(), self.load_macro()]):
                    pass

            delete_btn = tk.Button(
                macro_row,
                text="🗑️",
                font=("Arial", 10),
                bg="#e74c3c",
                fg="white",
                width=3,
                command=lambda name=macro_name: on_delete(name)
            )
            delete_btn.pack(side="right", padx=5, pady=2)


        btn_frame = tk.Frame(modal, bg="#f7f7f7")
        btn_frame.pack(pady=(10, 20))

        def cargar():
            macro_name = selected_macro.get()
            if not macro_name:
                messagebox.showwarning("Validación", "Debe seleccionar una macro.")
                return

            if macro_name not in macros:
                messagebox.showerror("Error", "La macro seleccionada ya no existe.")
                return

            macro_data = macros[macro_name]

            # Cargar configuración de la macro en la tabla
            mc_data["command_configs"] = dict(macro_data["command_configs"])
            mc_data["last_state"] = dict(macro_data.get("last_state", {}))
            self.delta_time_var.set(macro_data.get("delta_time", 0.5))
            
            self.rebuild_command_table()
            modal.destroy()

        cargar_btn = tk.Button(
            btn_frame,
            text="Cargar",
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            command=cargar,
            width=10
        )
        cargar_btn.pack(side="left", padx=10)

        cancelar_btn = tk.Button(
            btn_frame,
            text="Cancelar",
            font=("Arial", 10, "bold"),
            bg="#e74c3c",
            fg="white",
            command=modal.destroy,
            width=10
        )
        cancelar_btn.pack(side="right", padx=10)

    def delete_macro(self, mc_data, macro_name, callback=None):
        """Elimina una macro del microcontrolador
        
        Args:
            mc_data: Datos del microcontrolador
            macro_name: Nombre de la macro a eliminar
            callback: Función opcional a ejecutar después de eliminar
        """
        if messagebox.askyesno("Confirmar eliminación", f"¿Eliminar la macro '{macro_name}'?"):
            if "macros" in mc_data and macro_name in mc_data["macros"]:
                del mc_data["macros"][macro_name]
                self.update_db_stats()
                messagebox.showinfo("Éxito", f"Macro '{macro_name}' eliminada correctamente.")
                
                # Ejecutar callback si existe
                if callback:
                    callback()
                
                return True
        return False

    def create_menu(self):
        """Crea el menú principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)

    def open_add_command_modal(self):
        """Abre un modal para agregar comandos"""
        selected_mc_display = self.mc_var.get()
        selected_mc = self.get_mac_from_selection(selected_mc_display)
        if not selected_mc:
            messagebox.showwarning("Validación", "Debe seleccionar un Micro Controlador para gestionar comandos.")
            return

        # Buscar el MC seleccionado
        mc_key = None
        mc_data = None
        for key, data in self.mc_registered.items():
            if data.get("mac_destiny") == selected_mc:
                mc_key = key
                mc_data = data
                break
        if not mc_data:
            messagebox.showwarning("Validación", "Micro Controlador no encontrado.")
            return

        # Universo de comandos
        all_commands = list(self.command_configs.keys())
        # Contar instancias actuales de cada comando
        current_commands = list(mc_data.get("command_configs", {}).keys())
        command_counts = {}
        for cmd in all_commands:
            # Contar instancias: buscar keys que sean exactamente cmd o que empiecen con "cmd#"
            count = 0
            for key in current_commands:
                base_cmd = key.split('#')[0] if '#' in key else key
                if base_cmd == cmd:
                    count += 1
            command_counts[cmd] = count

        modal = tk.Toplevel(self.root)
        modal.title("Gestionar Comandos")
        modal.transient(self.root)
        modal.grab_set()
        modal.resizable(False, False)
        modal.configure(bg="#f7f7f7")

        # Usar el método helper para centrar
        self.center_modal_on_parent(modal, 400, 520)  # <-- CAMBIO AQUÍ
        
        tk.Label(modal, text="Gestionar comandos del microcontrolador", font=("Arial", 12, "bold"), bg="#f7f7f7").pack(pady=(20, 10))

       # Frame con scroll para la lista de comandos
        canvas_frame = tk.Frame(modal, bg="#f7f7f7")
        canvas_frame.pack(fill="both", expand=True, padx=20, pady=10)

        canvas = tk.Canvas(canvas_frame, bg="#f7f7f7", highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        cb_frame = tk.Frame(canvas, bg="#f7f7f7")

        cb_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=cb_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Variables para los checkboxes e instancias
        command_vars = {}
        instance_vars = {}

        # Checkbox seleccionar/deseleccionar todos
        select_all_var = tk.BooleanVar(value=False)
        def toggle_all():
            value = select_all_var.get()
            for var in command_vars.values():
                var.set(value)

        header_frame = tk.Frame(cb_frame, bg="#f7f7f7")
        header_frame.pack(fill="x", pady=(0, 8))

        select_all_cb = tk.Checkbutton(
            header_frame,
            text="Seleccionar/Deseleccionar todos",
            variable=select_all_var,
            command=toggle_all,
            anchor="w",
            bg="#f7f7f7",
            font=("Arial", 10, "bold"),
            width=35
        )
        select_all_cb.grid(row=0, column=0, sticky="w")

        tk.Label(header_frame, text="Instancias", font=("Arial", 10, "bold"), bg="#f7f7f7").grid(row=0, column=1, padx=(10, 0))

        # Listado de comandos con checkboxes e inputs de instancias
        for cmd_name in all_commands:
            var = tk.BooleanVar(value=command_counts[cmd_name] > 0)
            command_vars[cmd_name] = var
            
            instance_var = tk.IntVar(value=max(1, command_counts[cmd_name]))
            instance_vars[cmd_name] = instance_var

            row_frame = tk.Frame(cb_frame, bg="#f7f7f7")
            row_frame.pack(fill="x", pady=2)

            cb = tk.Checkbutton(row_frame, text=cmd_name, variable=var, anchor="w", bg="#f7f7f7", width=35)
            cb.grid(row=0, column=0, sticky="w")

            spinbox = tk.Spinbox(
                row_frame,
                from_=1,
                to=100,
                textvariable=instance_var,
                width=5,
                justify="center"
            )
            spinbox.grid(row=0, column=1, padx=(10, 0))

        btn_frame = tk.Frame(modal, bg="#f7f7f7")
        btn_frame.pack(fill="x", pady=(20, 20))

        def aceptar():
            # Construir nueva lista de comandos con repeticiones
            new_command_list = []
            
            for cmd in all_commands:
                if command_vars[cmd].get():  # Si está seleccionado
                    instances = instance_vars[cmd].get()
                    for _ in range(instances):
                        new_command_list.append(cmd)
            
            # Construir command_configs manteniendo el orden y permitiendo duplicados
            new_command_configs = {}
            for i, cmd in enumerate(new_command_list):
                # Usar un key único para cada instancia
                if new_command_list.count(cmd) > 1:
                    # Contar cuántas veces ya apareció este comando
                    count_before = new_command_list[:i].count(cmd)
                    key = f"{cmd}#{count_before + 1}"
                else:
                    key = cmd
                new_command_configs[key] = self.command_configs[cmd]
            
            mc_data["command_configs"] = new_command_configs

            # Actualizar last_state
            last_state = mc_data.get("last_state", {})
            new_last_state = {}
            for key in new_command_configs.keys():
                # Extraer el comando base (sin el #N)
                base_cmd = key.split('#')[0] if '#' in key else key
                # Si ya existía un estado para este comando, mantenerlo
                if key in last_state:
                    new_last_state[key] = last_state[key]
                elif base_cmd in last_state:
                    new_last_state[key] = last_state[base_cmd]
                else:
                    new_last_state[key] = ""
            
            # Limpiar estados de comandos que ya no existen
            mc_data["last_state"] = new_last_state

            self.update_db_stats()
            self.rebuild_command_table()
            modal.destroy()

        agregar_btn = tk.Button(btn_frame, text="Agregar", font=("Arial", 10, "bold"), bg="#27ae60", fg="white", command=aceptar)
        agregar_btn.pack(side="left", padx=(40, 10), ipadx=10)

        cancelar_btn = tk.Button(btn_frame, text="Cancelar", font=("Arial", 10, "bold"), bg="#e74c3c", fg="white", command=modal.destroy)
        cancelar_btn.pack(side="right", padx=(10, 40), ipadx=10)

    def center_modal_on_parent(self, modal, width, height):
        """Centra un modal sobre la ventana principal (parent)
        
        Args:
            modal: Ventana Toplevel a centrar
            width: Ancho del modal
            height: Alto del modal
        """
        modal.update_idletasks()
        
        # Obtener posición y tamaño de la ventana principal
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_width = self.root.winfo_width()
        parent_height = self.root.winfo_height()
        
        # Calcular posición centrada sobre el parent
        x = parent_x + (parent_width // 2) - (width // 2)
        y = parent_y + (parent_height // 2) - (height // 2)
        
        modal.geometry(f"{width}x{height}+{x}+{y}")
    
    def toggle_command_state(self, cmd_name, state):
        """Maneja el toggle de botones ON/OFF/HIGH/LOW/GLOBAL/LOCAL para cada comando"""
        cmd_state = self.commands_state[cmd_name]
        on_btn = cmd_state["on_btn"]
        off_btn = cmd_state.get("off_btn")  # Puede ser None

        # Obtener las keys del comando
        base_cmd = cmd_name.split('#')[0] if '#' in cmd_name else cmd_name
        btn_keys = list(self.command_configs[base_cmd].keys())
        btn1_text = btn_keys[0] if len(btn_keys) > 0 else "ON"
        btn2_text = btn_keys[1] if len(btn_keys) > 1 else "OFF"
        
        # Comandos de un solo botón
        single_button_commands = ["X_FF_Reset", "X_02_TestTrigger", "X_03_RO_Single"]

        # Si presiona el mismo botón que ya está activo, desactivarlo
        if cmd_state["state"] == state:
            cmd_state["state"] = None
            on_btn.config(bg="#e0e0e0", relief="raised")
            if off_btn:
                off_btn.config(bg="#e0e0e0", relief="raised")
            self.add_response(f"🔘 {cmd_name}: Desactivado")
        else:
            # Activar el botón presionado
            cmd_state["state"] = state

            if state == btn1_text:  # Botón 1 (ON/HIGH/GLOBAL)
                on_btn.config(bg="#27ae60", relief="sunken")
                if off_btn:
                    off_btn.config(bg="#e0e0e0", relief="raised")
                self.add_response(f"✓ {cmd_name}: {state} seleccionado")
            elif not (base_cmd in single_button_commands):  # Botón 2 (solo si existe)
                if off_btn:
                    off_btn.config(bg="#e74c3c", relief="sunken")
                on_btn.config(bg="#e0e0e0", relief="raised")
                self.add_response(f"✗ {cmd_name}: {state} seleccionado")

    def send_selected_commands(self):
        """Envía todos los comandos seleccionados con delta de tiempo en el orden visual configurado"""
        # Obtener MC destino
        selected_mc_display = self.mc_var.get()
        selected_mc = self.get_mac_from_selection(selected_mc_display)

        if not selected_mc:
            messagebox.showwarning(
                "Validación", "Debe seleccionar un Micro Controlador"
            )
            return
        
        # Guardar delta_time y estados en el MC seleccionado
        delta_time = self.delta_time_var.get()
        for mc_key, mc_data in self.mc_registered.items():
            if mc_data.get("mac_destiny") == selected_mc:
                mc_data["delta_time"] = delta_time
                command_configs = mc_data.get("command_configs", {})
                last_state = {}
                
                # Comandos automáticos
                auto_commands = ["X_FF_Reset", "X_02_TestTrigger", "X_03_RO_Single"]
                repeatable_commands = ["X_02_TestTrigger", "X_03_RO_Single"]
                
                for cmd_name in command_configs.keys():
                    base_cmd = cmd_name.split('#')[0] if '#' in cmd_name else cmd_name
                    cmd_state = self.commands_state.get(cmd_name, {})
                    
                    # Para comandos automáticos, guardar "ON" si está enabled
                    if base_cmd in auto_commands:
                        if cmd_state.get("enabled", tk.BooleanVar()).get():
                            last_state[cmd_name] = "ON"
                        else:
                            last_state[cmd_name] = ""
                    else:
                        # Para comandos normales, guardar el estado seleccionado
                        last_state[cmd_name] = cmd_state.get("state", "")
                    
                    # Guardar repeticiones si aplica
                    if base_cmd in repeatable_commands and "repetitions" in cmd_state:
                        last_state[f"{cmd_name}_reps"] = cmd_state["repetitions"].get()
                
                mc_data["last_state"] = last_state
                break

        self.update_db_stats()

        # Obtener MAC origen e interfaz
        mac_origen = None
        interface = None

        for mac_src, data in self.mc_registered.items():
            if data.get("mac_destiny") == selected_mc:
                mac_origen = mac_src
                interface = data.get("interface_destiny")
                break

        if not mac_origen or not interface:
            messagebox.showwarning("Validación", "MC no está registrado correctamente")
            return

        # Comandos automáticos
        auto_commands = ["X_FF_Reset", "X_02_TestTrigger", "X_03_RO_Single"]
        # Comandos que se pueden repetir
        repeatable_commands = ["X_02_TestTrigger", "X_03_RO_Single"]
    
        # Recolectar comandos habilitados en el orden visual
        commands_to_send = []
        for row in self.command_rows:
            cmd_name = row["cmd_name"]
            cmd_state = self.commands_state[cmd_name]
            base_cmd = cmd_name.split('#')[0] if '#' in cmd_name else cmd_name
            
            # Para comandos automáticos, solo verificar si está enabled
            if base_cmd in auto_commands:
                if cmd_state["enabled"].get():
                    appendix_key = self.command_configs[base_cmd]["ON"]
                    
                    # Obtener número de repeticiones si aplica
                    repetitions = 1
                    if base_cmd in repeatable_commands and "repetitions" in cmd_state:
                        repetitions = cmd_state["repetitions"].get()
                    
                    commands_to_send.append(
                        {
                            "name": cmd_name,
                            "state": "ON",
                            "appendix_key": appendix_key,
                            "repetitions": repetitions,
                        }
                    )
            else:
                # Para comandos normales, verificar enabled y state
                if cmd_state["enabled"].get() and cmd_state["state"]:
                    appendix_key = self.command_configs[base_cmd][cmd_state["state"]]
                    commands_to_send.append(
                        {
                            "name": cmd_name,
                            "state": cmd_state["state"],
                            "appendix_key": appendix_key,
                            "repetitions": 1,
                        }
                    )

        if not commands_to_send:
            messagebox.showwarning("Validación", "Debe seleccionar al menos un comando")
            return

        # Obtener delta de tiempo
        delta_time = self.delta_time_var.get()

        # Confirmación solo si el checkbox está marcado
        if self.show_summary_var.get():
            cmd_list = "\n".join(
                [f"  • {c['appendix_key']}" for c in commands_to_send]
            )
            info_msg = f"""
    Se enviarán {len(commands_to_send)} comando(s):
    {cmd_list}

    Delta de tiempo: {delta_time}s
    MC Destino: {selected_mc}
    Interfaz: {interface}
            """.strip()

            if not messagebox.askyesno("Ventana Resumen", info_msg):
                return

        # Cambiar botón a modo "Cancelar"
        self.sending_commands = True
        self.cancel_sending = False
        self.send_commands_btn.config(text="⏹ Cancelar", bg="#e74c3c")

        self.add_response("=" * 50)
        self.add_response(f"📡 Enviando {len(commands_to_send)} comando(s)")

        # Enviar comandos con delay
        def send_all():
            cmd_index = 1
            total_commands = sum(c["repetitions"] for c in commands_to_send)
            
            for cmd_info in commands_to_send:
                repetitions = cmd_info["repetitions"]
                
                for rep in range(repetitions):
                    # Verificar cancelación
                    if self.cancel_sending:
                        self.add_response(f"⚠️ Envío cancelado después de {cmd_index-1}/{total_commands} comandos")
                        break
                    
                    if cmd_index > 1:
                        # Verificar cancelación durante el delay
                        for _ in range(int(delta_time * 10)):
                            if self.cancel_sending:
                                self.add_response(f"⚠️ Envío cancelado después de {cmd_index-1}/{total_commands} comandos")
                                break
                            time.sleep(0.1)
                        
                        if self.cancel_sending:
                            break
                    
                    # Mostrar número de repetición si aplica
                    rep_info = f" (rep {rep+1}/{repetitions})" if repetitions > 1 else ""
                    send_command_packet(cmd_info, cmd_index, total_commands, rep_info)
                    cmd_index += 1
                
                if self.cancel_sending:
                    break

            if not self.cancel_sending:
                self.add_response("✓ Todos los comandos enviados")
            
            self.add_response("=" * 50)
            
            # Restaurar botón
            self.sending_commands = False
            self.cancel_sending = False
            self.send_commands_btn.config(text="Enviar Comandos", bg="#3498db")
        
        def send_command_packet(cmd_info, index, total, rep_info=""):
            """Envía un paquete individual"""
            try:
                appendix = appendix_dict.get(cmd_info["appendix_key"])

                # Construir paquete
                mac_origen_bytes = bytes.fromhex(mac_origen.replace(":", ""))
                mac_destino_bytes = bytes.fromhex(selected_mc.replace(":", ""))
                payload_length = 7
                length_bytes = payload_length.to_bytes(2, byteorder="big")
                padding_bytes = b"\x00\x00\x00\x00"
                constant_bytes = b"\x02\x03"

                packet = (
                    mac_destino_bytes
                    + mac_origen_bytes
                    + length_bytes
                    + padding_bytes
                    + constant_bytes
                    + appendix
                )

                # Enviar
                scapy_packet = Raw(load=packet)
                sendp(scapy_packet, iface=interface, verbose=False)

                self.add_response(
                    f"✓ [{index}/{total}] {cmd_info['appendix_key']}{rep_info} enviado"
                )

            except Exception as e:
                self.add_response(f"✗ Error en {cmd_info['appendix_key']}: {str(e)}")

        # Ejecutar en thread
        threading.Thread(target=send_all, daemon=True).start()

    def refresh_mc_list(self):
        """Actualiza la lista de interfaces ethernet conectadas y sus MACs"""

        # Limpiar datos previos
        self.mc_available = {}

        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()

        for iface_name, addrs in interfaces.items():
            # Filtros básicos
            if iface_name == "lo":  # Loopback
                continue
            if any(
                iface_name.startswith(prefix)
                for prefix in ["vir", "docker", "br-", "veth", "vmnet", "vboxnet"]
            ):
                continue
            if "wl" in iface_name.lower() or "wifi" in iface_name.lower():  # WiFi
                continue

            # Verificar que la interfaz esté UP
            if iface_name in stats and not stats[iface_name].isup:
                continue

            # Buscar MAC
            mac = None
            for addr in addrs:
                if (
                    getattr(addr, "family", None) == psutil.AF_LINK
                    or getattr(addr, "family", None) == 17
                ):
                    mac = addr.address
                    break

            # Solo agregar si tiene MAC y no es 00:00:00:00:00:00
            if mac and mac != "00:00:00:00:00:00":
                self.mc_available[mac] = iface_name
                display_text = f"{iface_name} (MAC: {mac})"

        # # Para debbuging
        # print("Interfaces ethernet detectadas:")
        # for mac, iface in self.mc_available.items():
        #     print(f"{iface}: {mac}")

        self.frames_sent_label.config(text=str(len(self.mc_available)))

    def get_mc_display_list(self):
        """Retorna lista formateada de MCs registrados: label | mac"""
        display_list = []
        for mac_origen in self.mc_available.keys():
            if mac_origen in self.mc_registered:
                label = self.mc_registered[mac_origen].get("label", "Sin etiqueta")
                mac_destino = self.mc_registered[mac_origen].get("mac_destiny", "N/A")
                display_list.append(f"{label} | {mac_destino}")
            else:
                display_list.append(f"No registrado")
        return display_list

    def get_mac_from_selection(self, selection):
        """Extrae la MAC de la selección del combobox"""
        if " | " in selection:
            return selection.split(" | ")[1]
        return None

    def refresh_dashboard_mc_table(self):
        """Refresca la lista y tabla de micro controladores en el dashboard"""
        self.refresh_mc_list()
        # Actualizar combobox de MAC origen
        if hasattr(self, "mac_origen_combo"):
            self.mac_origen_combo["values"] = list(self.mc_available.keys())

        # Actualizar combobox de MC destino (comandos)
        if hasattr(self, "mc_combo"):
            self.mc_combo["values"] = self.get_mc_display_list()

        # Limpiar la tabla
        for row in self.mc_table.get_children():
            self.mc_table.delete(row)

        # Insertar datos actualizados
        for mac_source, interfaz in self.mc_available.items():
            if mac_source in self.mc_registered:
                mac_destiny = self.mc_registered[mac_source].get("mac_destiny", "N/A")
                interface_destiny = self.mc_registered[mac_source].get(
                    "interface_destiny", "N/A"
                )
                label = self.mc_registered[mac_source].get("label", "Sin Label")
            else:
                mac_destiny = "No registrado"
                interface_destiny = "N/A"
                label = "N/A"

            self.mc_table.insert(
                "",
                "end",
                values=(interfaz, mac_source, mac_destiny, interface_destiny, label),
            )

    def register_mc(self):
        """Procesa el registro de un micro controlador"""

        mac_origen = self.mac_origen_var.get()
        mac_destino = self.mac_destino_var.get().strip().lower()
        interface_destino = self.interface_destino_var.get().strip()
        label = self.label_var.get().strip()

        # Validaciones
        if not mac_origen or mac_origen == "Seleccione MAC origen...":
            messagebox.showwarning("Validación", "Debe seleccionar una MAC de origen")
            return

        if not mac_destino:
            messagebox.showwarning("Validación", "Debe ingresar una MAC de destino")
            return

        if not interface_destino:
            messagebox.showwarning(
                "Validación", "Debe ingresar una interfaz de destino"
            )
            return

        # Validar formato MAC (soporta : y - como separadores)
        mac_pattern = r"^([0-9a-f]{2}[:-]){5}[0-9a-f]{2}$"
        if not re.match(mac_pattern, mac_destino):
            messagebox.showerror(
                "Validación", "Formato de MAC inválido\nUse formato: fe:80:ab:cd:12:34"
            )
            return

        # Normalizar formato (usar : como separador)
        mac_destino = mac_destino.replace("-", ":")

        # Registrar en diccionario
        self.mc_registered[mac_origen] = {
            "mac_destiny": mac_destino,
            "interface_destiny": interface_destino,
            "label": label if label else "Sin etiqueta",
            "command_configs": dict(self.command_configs)
        }

        # Limpiar formulario
        self.mac_origen_var.set("Seleccione MAC origen...")
        self.mac_destino_var.set("")
        self.interface_destino_var.set("")
        self.label_var.set("")

        # Refrescar tabla
        self.refresh_dashboard_mc_table()

        try:
            self.update_db_stats()
            messagebox.showinfo(
                "Éxito",
                f"Micro Controlador registrado:\n{mac_origen} → {mac_destino} ({interface_destino})",
            )
        except Exception:
            messagebox.showinfo(
                "Error",
                f"No fue posible asociar el micro controlador:\n{mac_origen} → {mac_destino} ({interface_destino})",
            )

    def create_menu(self):
        """Crea el menú principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        # file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)

    def add_response(self, response):
        """Añade una respuesta al área de texto"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.response_text.insert(tk.END, f"[{timestamp}] {response}\n")
        self.response_text.see(tk.END)

    # Metodos para la db #
    def update_db_stats(self):
        """Actualiza o inserta los datos de microcontroladores registrados en db.json"""
        db_path = db_json

        # Estructura para guardar
        if not hasattr(self, "db") or not isinstance(self.db, dict):
            self.db = {}

        # Actualiza los datos de microcontroladores registrados
        self.db["mc_registered"] = self.mc_registered

        # Guarda en disco (sobrescribe)
        try:
            with open(db_path, "w", encoding="utf-8") as f:
                json.dump(self.db, f, indent=4)
        except Exception as e:
            print(f"Error al guardar en {db_path}: {e}")


def main():
    """Función principal para ejecutar la aplicación"""
    root = tk.Tk()
    app = McControlApp(root)

    def on_closing():
        """Maneja el cierre de la aplicación"""
        app.running = False
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
