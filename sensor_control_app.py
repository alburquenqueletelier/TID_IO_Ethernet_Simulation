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

        # Contadores y estadísticas
        self.mc_available = {}  # keys: mac_source, values: interfaces
        self.mc_registered = (
            {}
        )  # keys: mac_source, values: dict {  mac_destiny, interface_destiny, label}
        self.frames_sent = 0
        self.frames_received = 0

        # Inicializar base de datos
        self.init_database()

        # Crear interfaz
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
        # Encontrar índices
        source_idx = None
        target_idx = None

        for i, row_data in enumerate(self.command_rows):
            if row_data["cmd_name"] == source_cmd:
                source_idx = i
            if row_data["cmd_name"] == target_cmd:
                target_idx = i

        if source_idx is None or target_idx is None:
            return

        # Reordenar en la lista
        item = self.command_rows.pop(source_idx)
        self.command_rows.insert(target_idx, item)

        # Reordenar también en command_configs para mantener consistencia
        configs_list = list(self.command_configs.items())
        config_item = configs_list.pop(source_idx)
        configs_list.insert(target_idx, config_item)
        self.command_configs = dict(configs_list)

        # Actualizar la UI
        self.rebuild_command_table()

        self.add_response(
            f"✓ Orden actualizado: {source_cmd} movido a posición de {target_cmd}"
        )

    def rebuild_command_table(self):
        """Reconstruye la tabla de comandos con el nuevo orden y carga last_state según MC seleccionado"""
        # Destruir todas las filas actuales
        for row_data in self.command_rows:
            row_data["frame"].destroy()
        self.command_rows.clear()

        # Obtener el MC destino seleccionado
        selected_mc_display = self.mc_var.get()
        selected_mc = self.get_mac_from_selection(selected_mc_display) if selected_mc_display else None

        # Buscar last_state del MC seleccionado
        last_state = {}
        for data in self.mc_registered.values():
            if data.get("mac_destiny") == selected_mc:
                last_state = data.get("last_state", {})
                break

        # Recrear filas en el nuevo orden
        for idx, (cmd_name, cmd_config) in enumerate(self.command_configs.items()):
            bg_color = "#f7f7f7" if idx % 2 == 0 else "#e3e3e3"
            row_frame = tk.Frame(self.commands_table_frame, relief="ridge", borderwidth=1, bg=bg_color)
            row_frame.pack(fill="x")

            # Inicializar estado
            self.commands_state[cmd_name] = {
                "enabled": tk.BooleanVar(value=False),
                "state": None,
            }

            # Checkbox
            checkbox = tk.Checkbutton(
                row_frame, variable=self.commands_state[cmd_name]["enabled"], bg=bg_color
            )
            checkbox.grid(row=0, column=0, padx=5)

            # Nombre del comando
            tk.Label(
                row_frame, text=cmd_name, width=16, font=("Arial", 9), bg=bg_color
            ).grid(row=0, column=1)

            # Obtener llaves para los botones (por ejemplo: ["ON", "OFF"] o ["LOW", "HIGH"])
            btn_keys = list(cmd_config.keys())
            btn1_text = btn_keys[0] if len(btn_keys) > 0 else "ON"
            btn2_text = btn_keys[1] if len(btn_keys) > 1 else "OFF"

            # Botón 1 (ON/LOW)
            on_btn = tk.Button(
                row_frame,
                text=btn1_text,
                width=8,
                bg="#e0e0e0",
                command=lambda cmd=cmd_name, state=btn1_text: self.toggle_command_state(cmd, state),
            )
            on_btn.grid(row=0, column=2, padx=2, pady=2)

            # Botón 2 (OFF/HIGH)
            off_btn = tk.Button(
                row_frame,
                text=btn2_text,
                width=8,
                bg="#e0e0e0",
                command=lambda cmd=cmd_name, state=btn2_text: self.toggle_command_state(cmd, state),
            )
            off_btn.grid(row=0, column=3, padx=2, pady=2)

            # Guardar referencias de botones
            self.commands_state[cmd_name]["on_btn"] = on_btn
            self.commands_state[cmd_name]["off_btn"] = off_btn

            # Cargar estado guardado si existe
            saved_state = last_state.get(cmd_name)
            if saved_state == btn1_text:
                self.commands_state[cmd_name]["state"] = btn1_text
                on_btn.config(bg="#27ae60", relief="sunken")
                off_btn.config(bg="#e0e0e0", relief="raised")
            elif saved_state == btn2_text:
                self.commands_state[cmd_name]["state"] = btn2_text
                off_btn.config(bg="#e74c3c", relief="sunken")
                on_btn.config(bg="#e0e0e0", relief="raised")
            else:
                # Ningún estado guardado
                on_btn.config(bg="#e0e0e0", relief="raised")
                off_btn.config(bg="#e0e0e0", relief="raised")

            # Guardar referencia de la fila
            self.command_rows.append({"frame": row_frame, "cmd_name": cmd_name})

            # Setup drag and drop
            self.setup_drag_and_drop(row_frame, cmd_name)

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

    def create_login_screen(self):
        """Crea la pantalla de login"""
        self.login_frame = tk.Frame(self.root, bg="#2c3e50", width=400, height=300)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Título
        title_label = tk.Label(
            self.login_frame,
            text="Sistema de Control de Micro Controladores",
            font=("Arial", 16, "bold"),
            fg="white",
            bg="#2c3e50",
        )
        title_label.pack(pady=30)

        # Usuario
        tk.Label(self.login_frame, text="Usuario:", fg="white", bg="#2c3e50").pack()
        self.username_entry = tk.Entry(self.login_frame, width=20)
        self.username_entry.pack(pady=5)

        # Contraseña
        tk.Label(self.login_frame, text="Contraseña:", fg="white", bg="#2c3e50").pack()
        self.password_entry = tk.Entry(self.login_frame, show="*", width=20)
        self.password_entry.pack(pady=5)

        # Botón login
        login_btn = tk.Button(
            self.login_frame,
            text="Iniciar Sesión",
            command=self.login,
            bg="#3498db",
            fg="white",
            width=15,
            height=1,
        )
        login_btn.pack(pady=20)

        # Enfocar en el campo de usuario
        self.username_entry.focus()

        # Bind Enter key
        self.root.bind("<Return>", lambda event: self.login())

    def login(self):
        """Verifica credenciales y accede a la aplicación"""
        username = self.username_entry.get()
        password = self.password_entry.get()

        # Credenciales hardcodeadas (solo para desarrollo)
        if username == "admin" and password == "sensor123":
            self.admin_in = True
            self.login_frame.destroy()
            self.create_main_interface()
        else:
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")

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
        """Crea la pestaña del dashboard"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")

        ###
        # Frame superior para Gestionar Micro Controladores
        stats_frame = tk.LabelFrame(
            dashboard_frame,
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
        )  # <-- AGREGADA COLUMNA
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

        # FORMULARIO DE REGISTRO
        register_frame = tk.LabelFrame(
            dashboard_frame,
            text="Registrar Micro Controlador",
            font=("Arial", 12, "bold"),
        )
        register_frame.pack(fill="x", padx=10, pady=10)

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

        # Fila 3: Interfaz Destino (NUEVA)
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

        # Fila 4: Label (antes era Fila 3)
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

        # Área de respuestas/log
        response_frame = tk.LabelFrame(
            dashboard_frame, text="Respuestas / Log", font=("Arial", 10, "bold")
        )
        response_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.response_text = scrolledtext.ScrolledText(
            response_frame, height=8, font=("Consolas", 10)
        )
        self.response_text.pack(fill="both", expand=True)

    def create_commands_tab(self):
        """Crea la pestaña de comandos con scroll"""
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

        canvas.bind(
            "<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width)
        )

        canvas_window = canvas.create_window(
            (0, 0), window=scrollable_frame, anchor="nw"
        )  # <-- GUARDA LA REFERENCIA
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Scroll con rueda del mouse
        def _on_mousewheel(event):
            # Windows y macOS usan event.delta, Linux usa event.num
            if hasattr(event, "delta"):
                if event.delta > 0:
                    canvas.yview_scroll(-1, "units")
                elif event.delta < 0:
                    canvas.yview_scroll(1, "units")
            else:
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows/macOS
        canvas.bind_all("<Button-4>", _on_mousewheel)  # Linux scroll up
        canvas.bind_all("<Button-5>", _on_mousewheel)  # Linux scroll down

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

        # Frame izquierdo: contendrá ambos formularios uno sobre otro
        forms_left_frame = tk.Frame(main_row_container)
        forms_left_frame.pack(side="left", fill="both", expand=True)

        # Frame para X_02_TestTrigger (mitad superior)
        form_frame = tk.LabelFrame(forms_left_frame, text="X_02_TestTrigger")
        form_frame.pack(fill="both", expand=True, padx=(0, 5), pady=(0, 2))

        form_container = tk.Frame(form_frame)
        form_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Fila 1: Número de ejecuciones
        executions_row = tk.Frame(form_container)
        executions_row.pack(fill="x", pady=3)

        tk.Label(
            executions_row,
            text="Ejecuciones:",
            font=("Arial", 9, "bold"),
            width=12,
            anchor="w",
        ).pack(side="left")

        self.executions_var = tk.IntVar(value=1)
        executions_spinbox = tk.Spinbox(
            executions_row,
            from_=1,
            to=100,
            textvariable=self.executions_var,
            width=8,
            justify="center",
        )
        executions_spinbox.pack(side="left", padx=(5, 3))

        tk.Label(executions_row, text="(1-100)", fg="gray", font=("Arial", 7)).pack(
            side="left"
        )

        # Fila 2: Intervalo de tiempo
        interval_row = tk.Frame(form_container)
        interval_row.pack(fill="x", pady=3)

        tk.Label(
            interval_row,
            text="Intervalo (seg):",
            font=("Arial", 9, "bold"),
            width=12,
            anchor="w",
        ).pack(side="left")

        self.interval_var = tk.DoubleVar(value=1.0)
        interval_spinbox = tk.Spinbox(
            interval_row,
            from_=0.1,
            to=3600.0,
            increment=0.5,
            textvariable=self.interval_var,
            width=8,
            justify="center",
            format="%.1f",
        )
        interval_spinbox.pack(side="left", padx=(5, 3))

        tk.Label(interval_row, text="(0.1-3600)", fg="gray", font=("Arial", 7)).pack(
            side="left"
        )

        # Botón de envío
        button_row = tk.Frame(form_container)
        button_row.pack(fill="x", pady=(10, 0))

        send_form_btn = tk.Button(
            button_row,
            text="🚀 Enviar",
            command=lambda: self.process_command_form(
                "X_02_TestTrigger", self.executions_var.get(), self.interval_var.get()
            ),
            font=("Arial", 10, "bold"),
            bg="#2ecc71",
            fg="white",
            width=18,
            height=1,
            relief="raised",
        )
        send_form_btn.pack()

        # ============================================
        # NUEVO: Formulario X_03_RO_Single
        # ============================================
        # Frame para X_03_RO_Single (mitad inferior)
        ro_single_frame = tk.LabelFrame(forms_left_frame, text="X_03_RO_Single")
        ro_single_frame.pack(fill="both", expand=True, padx=(0, 5), pady=(2, 0))

        ro_single_form_container = tk.Frame(ro_single_frame)
        ro_single_form_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Fila 1: Número de ejecuciones
        ro_executions_row = tk.Frame(ro_single_form_container)
        ro_executions_row.pack(fill="x", pady=3)

        tk.Label(
            ro_executions_row,
            text="Ejecuciones:",
            font=("Arial", 9, "bold"),
            width=12,
            anchor="w",
        ).pack(side="left")

        self.ro_executions_var = tk.IntVar(value=1)
        ro_executions_spinbox = tk.Spinbox(
            ro_executions_row,
            from_=1,
            to=100,
            textvariable=self.ro_executions_var,
            width=8,
            justify="center",
        )
        ro_executions_spinbox.pack(side="left", padx=(5, 3))

        tk.Label(ro_executions_row, text="(1-100)", fg="gray", font=("Arial", 7)).pack(
            side="left"
        )

        # Fila 2: Intervalo de tiempo
        ro_interval_row = tk.Frame(ro_single_form_container)
        ro_interval_row.pack(fill="x", pady=3)

        tk.Label(
            ro_interval_row,
            text="Intervalo (seg):",
            font=("Arial", 9, "bold"),
            width=12,
            anchor="w",
        ).pack(side="left")

        self.ro_interval_var = tk.DoubleVar(value=1.0)
        ro_interval_spinbox = tk.Spinbox(
            ro_interval_row,
            from_=0.1,
            to=3600.0,
            increment=0.5,
            textvariable=self.ro_interval_var,
            width=8,
            justify="center",
            format="%.1f",
        )
        ro_interval_spinbox.pack(side="left", padx=(5, 3))

        tk.Label(ro_interval_row, text="(0.1-3600)", fg="gray", font=("Arial", 7)).pack(
            side="left"
        )

        # Botón de envío
        ro_button_row = tk.Frame(ro_single_form_container)
        ro_button_row.pack(fill="x", pady=(10, 0))

        send_ro_form_btn = tk.Button(
            ro_button_row,
            text="🚀 Enviar",
            command=lambda: self.process_command_form(
                "X_03_RO_Single",
                self.ro_executions_var.get(),
                self.ro_interval_var.get(),
            ),
            font=("Arial", 10, "bold"),
            bg="#2ecc71",
            fg="white",
            width=18,
            height=1,
            relief="raised",
        )
        send_ro_form_btn.pack()

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

        # Tabla de comandos
        table_frame = tk.Frame(commands_main_container)
        table_frame.pack(fill="both", expand=True)

        # Headers
        header_frame = tk.Frame(table_frame, relief="ridge", borderwidth=1)
        header_frame.pack(fill="x")

        tk.Label(header_frame, text="", width=5, font=("Arial", 8, "bold")).grid(
            row=0, column=0
        )
        tk.Label(
            header_frame, text="Comando", width=20, font=("Arial", 8, "bold")
        ).grid(row=0, column=1)
        tk.Label(
            header_frame, text="ON/HIGH/GLOBAL", width=15, font=("Arial", 8, "bold"), padx=10
        ).grid(row=0, column=2)
        tk.Label(header_frame, text="OFF/LOW/LOCAL", width=16, font=("Arial", 8, "bold")).grid(
            row=0, column=3
        )

        # Definir comandos con sus appendix
        self.command_configs = {
            "ReadOut": {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"},
            "Diagnosis": {"ON": "X_08_DIAG_", "OFF": "X_09_DIAG_DIS"},
            "TestTrigger Auto": {
                "ON": "X_FB_TTrig_Auto_EN",
                "OFF": "X_FC_TTrig_Auto_DIS",
            },
            "PETA8s Top": {"ON": "X_20_PwrDwnb_TOP_ON", "OFF": "X_21_PwrDwnb_TOP_OFF"},
            "PETAS8s Bottom": {
                "ON": "X_22_PwrDwnb_BOT_ON",
                "OFF": "X_23_PwrDwnb_BOT_OFF",
            },
            "Analog Buck": {"ON": "X_26_PwrEN_2V4D_ON", "OFF": "X_27_PwrEN_2V4D_OFF"},
            "3V1 Buck": {"ON": "X_28_PwrEN_3V1_ON", "OFF": "X_29_PwrEN_3V1_OFF"},
            "Analog LDO": {"ON": "X_2A_PwrEN_1V8A_ON", "OFF": "X_2B_PwrEN_1V8A_OFF"},
            "Fan Speed 0": {
            "HIGH": "X_E1_FanSpeed0_High", "LOW": "X_E0_FanSpeed0_Low"
            }
            #             "": b"\xe0",
            # "X_E1_FanSpeed0_High": b"\xe1",
            # "X_E2_FanSpeed1_Low": b"\xe2",
            # "X_E3_FanSpeed1_High": b"\xe3",
        }

        # Estado de comandos: {comando: {"enabled": bool, "state": "ON"/"OFF"/None}}
        self.commands_state = {}

        # Crear filas para cada comando
        # Inicializar lista para tracking de filas
        self.command_rows = []

        # Guardar referencia al frame contenedor
        self.commands_table_frame = table_frame

        for idx, (cmd_name, cmd_config) in enumerate(self.command_configs.items()):
            row_frame = tk.Frame(table_frame, relief="ridge", borderwidth=1, bg="white")
            row_frame.pack(fill="x")

            # Inicializar estado
            self.commands_state[cmd_name] = {
                "enabled": tk.BooleanVar(value=False),
                "state": None,
            }

            # Checkbox
            checkbox = tk.Checkbutton(
                row_frame, variable=self.commands_state[cmd_name]["enabled"]
            )
            checkbox.grid(row=0, column=0, padx=5)

            # Nombre del comando
            tk.Label(
                row_frame, text=cmd_name, width=16, font=("Arial", 9), bg="white"
            ).grid(row=0, column=1)

            # Obtener llaves para los botones (por ejemplo: ["ON", "OFF"] o ["LOW", "HIGH"])
            btn_keys = list(cmd_config.keys())
            btn1_text = btn_keys[0] if len(btn_keys) > 0 else "ON"
            btn2_text = btn_keys[1] if len(btn_keys) > 1 else "OFF"

            # Botón 1 (ON/LOW)
            on_btn = tk.Button(
                row_frame,
                text=btn1_text,
                width=8,
                bg="#e0e0e0",
                command=lambda cmd=cmd_name, state=btn1_text: self.toggle_command_state(cmd, state),
            )
            on_btn.grid(row=0, column=2, padx=2, pady=2)

            # Botón 2 (OFF/HIGH)
            off_btn = tk.Button(
                row_frame,
                text=btn2_text,
                width=8,
                bg="#e0e0e0",
                command=lambda cmd=cmd_name, state=btn2_text: self.toggle_command_state(cmd, state),
            )
            off_btn.grid(row=0, column=3, padx=2, pady=2)

            # Guardar referencias de botones
            self.commands_state[cmd_name]["on_btn"] = on_btn
            self.commands_state[cmd_name]["off_btn"] = off_btn

            # Guardar referencia de la fila
            self.command_rows.append({"frame": row_frame, "cmd_name": cmd_name})

            # Setup drag and drop
            self.setup_drag_and_drop(row_frame, cmd_name)

        # Botón enviar comandos
        send_commands_btn = tk.Button(
            commands_main_container,
            text="📤 Enviar Comandos Seleccionados",
            command=self.send_selected_commands,
            font=("Arial", 10, "bold"),
            bg="#3498db",
            fg="white",
            width=25,
            height=2,
            relief="raised",
        )
        send_commands_btn.pack(pady=(10, 0))

    def create_menu(self):
        """Crea el menú principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)

    def process_command_form(self, command, num_executions, time_interval):
        """Procesa el formulario de comandos con los datos ingresados"""
        # ...el resto del método igual, pero elimina las líneas:
        # num_executions = self.executions_var.get()
        # time_interval = self.interval_var.get()
        # Obtener datos del formulario

        selected_mc_display = self.mc_var.get()
        selected_mc = self.get_mac_from_selection(selected_mc_display)
        selected_command = command

        # Obtener MAC origen (del host hacia el MC) y interface destino
        mac_origen = None
        interface = None
        label = None

        for mac_src, data in self.mc_registered.items():
            if data.get("mac_destiny") == selected_mc:
                mac_origen = mac_src
                interface = data.get("interface_destiny")
                label = data.get("label")
                break

        # Validaciones
        if not mac_origen:
            messagebox.showwarning(
                "Validación", "Mac de origen sin mapear con mac de destino"
            )
            return

        if not interface:
            messagebox.showwarning("Validación", "Interfaz de destino no encontrada")
            return

        if not selected_command or selected_command == "Seleccione un comando...":
            messagebox.showwarning("Validación", "Debe seleccionar un tipo de comando")
            return

        if not selected_mc:
            if not messagebox.askyesno(
                "Sin Micro Controladores",
                "No hay Micro Controladores seleccionados. ¿Continuar con comando general?",
            ):
                return

        if num_executions < 1:
            messagebox.showwarning(
                "Validación", "El número de ejecuciones debe ser mayor a 0"
            )
            return

        if time_interval < 0.1:
            messagebox.showwarning(
                "Validación", "El intervalo debe ser mayor a 0.1 segundos"
            )
            return

        # Obtener el valor del diccionario
        command_value = self.commands.get(selected_command)

        # Mostrar información
        info_message = f"""
    Comando a ejecutar: {selected_command}
    Apéndice: {command_value}
    Micro Controladores objetivo: {label} | {selected_mc}
    Interfaz de envío: {interface}
    Número de ejecuciones: {num_executions}
    Intervalo entre ejecuciones: {time_interval} segundos
    Tiempo total estimado: {num_executions * time_interval:.1f} segundos
        """.strip()

        if messagebox.askyesno("Confirmar Ejecución", info_message):
            # Mostrar en el área de respuestas
            self.add_response(f"FORMULARIO PROCESADO:")
            self.add_response(
                f"Comando: {selected_command} | Apéndice: {command_value}"
            )
            self.add_response(f"MC Objetivo: {label} | {selected_mc}")
            self.add_response(f"Interfaz: {interface}")
            self.add_response(
                f"Ejecuciones: {num_executions}, Intervalo: {time_interval}s"
            )
            self.add_response("─" * 50)

            def process_form():
                try:
                    mac_origen_bytes = bytes.fromhex(mac_origen.replace(":", ""))
                    mac_destino_bytes = bytes.fromhex(selected_mc.replace(":", ""))
                    payload_length = 7
                    length_bytes = payload_length.to_bytes(2, byteorder="big")
                    padding_bytes = b"\x00\x00\x00\x00"
                    constant_bytes = b"\x02\x03"
                    appendix = appendix_dict.get(selected_command)

                    packet = (
                        mac_destino_bytes
                        + mac_origen_bytes
                        + length_bytes
                        + padding_bytes
                        + constant_bytes
                        + appendix
                    )

                    # Enviar paquete
                    scapy_packet = Raw(load=packet)
                    sendp(scapy_packet, iface=interface, verbose=False)

                    self.add_response(f"Comando enviado vía {interface}")

                except Exception as e:
                    self.add_response(f"Error: {str(e)}")

            # Ejecutar múltiples veces con intervalo
            for i in range(num_executions):
                if i > 0:
                    time.sleep(time_interval)
                threading.Thread(target=process_form, daemon=True).start()
                self.add_response(f"→ Ejecución {i+1}/{num_executions}")

    def toggle_switch(self, switch_name):
        """Maneja el cambio de estado de los switches con estado de carga"""

        # Obtener el estado actual
        is_on = self.switch_states[switch_name].get()

        # Obtener label de estado
        state_label_name = f"{switch_name.lower().replace(' ', '_')}_state_label"
        state_label = getattr(self, state_label_name, None)

        if not state_label:
            return

        # Mostrar estado "Cargando..."
        state_label.config(text="Cargando...", fg="orange")
        self.add_response(f"⏳ {switch_name} - Ejecutandose...")

        # Simular delay de comunicación con FPGA en thread separado
        def process_switch():
            # Enviar comando al MC
            self.send_toggle_switch_command(switch_name, is_on)

            time.sleep(1)  # Simular delay de respuesta

            # Actualizar interfaz en el thread principal
            self.root.after(
                0, lambda: self.update_switch_state(switch_name, is_on, state_label)
            )

        # Ejecutar en thread para no bloquear la UI
        threading.Thread(target=process_switch, daemon=True).start()

    def send_toggle_switch_command(self, switch_name, state):
        """
        Crea y envía el paquete de comando para el switch

        Formato del paquete:
        - 6 bytes: MAC destino
        - 6 bytes: MAC origen
        - 2 bytes: Largo del paquete
        - 4 bytes: 0x00 (reservados)
        - 2 bytes: 0x02 0x03 (constantes)
        - 1 byte: Apéndice (comando específico)
        """

        # Obtener MAC destino seleccionado
        selected_mc_display = self.mc_var.get()
        mac_destino = self.get_mac_from_selection(selected_mc_display)

        if not mac_destino:
            print("Error: No hay MC destino seleccionado")
            self.add_response("Error: Seleccione un MC destino")
            return None

        # Obtener MAC origen (del host hacia el MC)
        mac_origen = None
        for mac_src, data in self.mc_registered.items():
            if data.get("mac_destiny") == mac_destino:
                mac_origen = mac_src
                break

        if not mac_origen:
            print("Error: No se encontró MAC origen para el MC seleccionado")
            self.add_response("Error: MC no está registrado correctamente")
            return None

        # Determinar apéndice según switch y estado
        appendix_map = {
            "ReadOut": {
                True: appendix_dict.get("X_04_RO_ON"),
                False: appendix_dict.get("X_05_RO_OFF"),
            },
            "Diagnosis": {
                True: appendix_dict.get("X_08_DIAG_"),
                False: appendix_dict.get("X_09_DIAG_DIS"),
            },
        }

        appendix = appendix_map.get(switch_name, {}).get(state)

        # Construir el paquete
        try:
            # Convertir MACs de string a bytes
            mac_destino_bytes = bytes.fromhex(mac_destino.replace(":", ""))
            mac_origen_bytes = bytes.fromhex(mac_origen.replace(":", ""))

            # Largo del payload (4 bytes ceros + 2 bytes identificador + 1 byte apéndice = 7 bytes)
            payload_length = 7  # TODO: se debe calcular para apendice CPU.
            length_bytes = payload_length.to_bytes(
                2, byteorder="big"
            )  # big indian order (byte más significativo primero)

            # 4 bytes en 0
            padding_bytes = b"\x00\x00\x00\x00"

            # 2 bytes identificador
            constant_bytes = b"\x02\x03"

            # Construir paquete completo
            packet = (
                mac_destino_bytes  # 6 bytes
                + mac_origen_bytes  # 6 bytes
                + length_bytes  # 2 bytes
                + padding_bytes  # 4 bytes
                + constant_bytes  # 2 bytes
                + appendix  # 1 byte
            )

            packet_hex = packet.hex(":")
            self.add_response(f"Paquete {switch_name}: {packet_hex}")

            interface = self.mc_registered.get(mac_origen)["interface_destiny"]

            if not interface:
                print(f"Error: Interfaz no encontrada para MAC origen {mac_origen}")
                self.add_response("Error: Interfaz de envío no encontrada")
                return None

            # Log del paquete
            print(f"\n--- Paquete {switch_name} ({'ON' if state else 'OFF'}) ---")
            print(f"MAC Destino:    {mac_destino}")
            print(f"MAC Origen:     {mac_origen}")
            print(f"Largo (Type):   {payload_length} bytes")
            print(f"Apéndice:       {appendix.hex()}")
            print(f"Paquete completo: {packet_hex}")
            print(f"Total bytes:    {len(packet)}")

            # Envío del paquete raw a nivel de Capa 2 (Ethernet)
            # sendp() necesita un objeto de paquete de Scapy (Ether, Raw, etc.)
            # Para enviar los bytes exactos incluyendo la cabecera L2:
            scapy_packet = Raw(load=packet)
            sendp(scapy_packet, iface=interface, verbose=False)
            self.add_response(f"Comando enviado a través de {interface}")

            return packet  # Retornar los bytes del paquete

        except Exception as e:
            print(f"Error construyendo paquete: {e}")
            self.add_response(f"Error: {str(e)}")
            return None

    def update_switch_state(self, switch_name, is_on, state_label):
        """Actualiza el estado final del switch después del delay"""
        if is_on:
            print(f"{switch_name} Encendido")
            state_label.config(text="Encendido", fg="green")
            self.add_response(f"✓ {switch_name} Encendido")
        else:
            print(f"{switch_name} Apagado")
            state_label.config(text="Apagado", fg="red")
            self.add_response(f"✗ {switch_name} Apagado")

    def toggle_command_state(self, cmd_name, state):
        """Maneja el toggle de botones ON/OFF para cada comando"""
        cmd_state = self.commands_state[cmd_name]
        on_btn = cmd_state["on_btn"]
        off_btn = cmd_state["off_btn"]

        # Si presiona el mismo botón que ya está activo, desactivarlo
        if cmd_state["state"] == state:
            cmd_state["state"] = None
            on_btn.config(bg="#e0e0e0", relief="raised")
            off_btn.config(bg="#e0e0e0", relief="raised")
            self.add_response(f"🔘 {cmd_name}: Desactivado")
        else:
            # Activar el botón presionado
            cmd_state["state"] = state

            if state == "ON":
                on_btn.config(bg="#27ae60", relief="sunken")
                off_btn.config(bg="#e0e0e0", relief="raised")
                self.add_response(f"✓ {cmd_name}: ON seleccionado")
            else:  # OFF
                off_btn.config(bg="#e74c3c", relief="sunken")
                on_btn.config(bg="#e0e0e0", relief="raised")
                self.add_response(f"✗ {cmd_name}: OFF seleccionado")

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

        # Recolectar comandos habilitados en el orden visual
        commands_to_send = []
        for row in self.command_rows:
            cmd_name = row["cmd_name"]
            cmd_state = self.commands_state[cmd_name]
            if cmd_state["enabled"].get() and cmd_state["state"]:
                appendix_key = self.command_configs[cmd_name][cmd_state["state"]]
                commands_to_send.append(
                    {
                        "name": cmd_name,
                        "state": cmd_state["state"],
                        "appendix_key": appendix_key,
                    }
                )

        if not commands_to_send:
            messagebox.showwarning("Validación", "Debe seleccionar al menos un comando")
            return

        # Obtener delta de tiempo
        delta_time = self.delta_time_var.get()

        # Confirmación
        cmd_list = "\n".join(
            [f"  • {c['name']}: {c['state']}" for c in commands_to_send]
        )
        info_msg = f"""
    Se enviarán {len(commands_to_send)} comando(s):
    {cmd_list}

    Delta de tiempo: {delta_time}s
    MC Destino: {selected_mc}
    Interfaz: {interface}
        """.strip()

        if not messagebox.askyesno("Confirmar Envío", info_msg):
            return

        self.add_response("=" * 50)
        self.add_response(f"📡 Enviando {len(commands_to_send)} comando(s)")

        def send_command_packet(cmd_info, index, total):
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
                    f"✓ [{index}/{total}] {cmd_info['name']} {cmd_info['state']} enviado"
                )

            except Exception as e:
                self.add_response(f"✗ Error en {cmd_info['name']}: {str(e)}")

        # Enviar comandos con delay
        def send_all():
            for i, cmd_info in enumerate(commands_to_send, 1):
                if i > 1:
                    time.sleep(delta_time)
                send_command_packet(cmd_info, i, len(commands_to_send))

            self.add_response("✓ Todos los comandos enviados")
            self.add_response("=" * 50)

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
