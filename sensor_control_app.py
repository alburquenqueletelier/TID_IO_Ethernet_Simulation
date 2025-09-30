import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import psutil
import json
from datetime import datetime 
# import matplotlib.pyplot as plt
# from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict, deque
import queue

appendix_dict = {
    "X_00_CPU": b"00",
    "X_02_TestTrigger": b"02",
    "X_03_RO_Single": b"03",
    "X_04_RO_ON": b"04",
    "X_05_RO_OFF": b"05",
    "X_08_DIAG_": b"08",
    "X_09_DIAG_DIS": b"09",
    "X_F9_TTrig_Global": b"F9",
    "X_FA_TTrig_Local": b"FA",
    "X_FB_TTrig_Auto_EN": b"FB",
    "X_FC_TTrig_Auto_DIS": b"FC",
    "X_FF_Reset": b"FF",
    "X_20_PwrDwnb_TOP_ON": b"20",
    "X_21_PwrDwnb_TOP_OFF": b"21",
    "X_22_PwrDwnb_BOT_ON": b"22",
    "X_23_PwrDwnb_BOT_OFF": b"23",
    "X_24_PwrEN_2V4A_ON": b"24",
    "X_25_PwrEN_2V4A_OFF": b"25",
    "X_26_PwrEN_2V4D_ON": b"26",
    "X_27_PwrEN_2V4D_OFF": b"27",
    "X_28_PwrEN_3V1_ON": b"28",
    "X_29_PwrEN_3V1_OFF": b"29",
    "X_2A_PwrEN_1V8A_ON": b"2A",
    "X_2B_PwrEN_1V8A_OFF": b"2B",
    "X_E0_FanSpeed0_Low": b"E0",
    "X_E1_FanSpeed0_High": b"E1",
    "X_E2_FanSpeed1_Low": b"E2",
    "X_E3_FanSpeed1_High": b"E3",
}


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
        self.serial_connection = None
        self.data_queue = queue.Queue()
        self.running = False

        # Contadores y estadísticas
        self.mc_available = {}
        self.frames_sent = 0
        self.frames_received = 0
        self.sensor_data = deque(maxlen=1000)  # Últimos 1000 registros
        self.event_types = defaultdict(int)

        # Inicializar base de datos
        self.init_database()

        # Crear interfaz
        self.create_main_interface()

    def init_database(self):
        """Inicializa la base de datos SQLite"""
        self.conn = sqlite3.connect("sensor_data.db", check_same_thread=False)
        cursor = self.conn.cursor()

        # Tabla para datos de Micro Controladores
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                sensor_type TEXT,
                sensor_id TEXT,
                value REAL,
                unit TEXT,
                metadata TEXT
            )
        """
        )

        # Tabla para comunicación
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS communication_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                direction TEXT,
                data TEXT,
                frame_type TEXT
            )
        """
        )

        self.conn.commit()

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

        # Barra de estado
        self.status_bar = tk.Label(
            self.root, text="Desconectado", bd=1, relief=tk.SUNKEN, anchor=tk.W
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Menú
        self.create_menu()

    def create_dashboard_tab(self):
        """Crea la pestaña del dashboard"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")

        ###
        # Frame superior para Gestionar Micro Controladores
        stats_frame = tk.LabelFrame(
            dashboard_frame, text="Centro de Micro Controladores", font=("Arial", 12, "bold")
        )
        stats_frame.pack(fill="x", padx=10, pady=5)

        # Crear grid para gestor de Micro Controladores
        stats_grid = tk.Frame(stats_frame)
        stats_grid.pack(fill="x", padx=10, pady=10)

        # Tramas enviadas
        tk.Label(
            stats_grid, text="Micro Controladores Conectados", font=("Arial", 10, "bold")
        ).grid(row=0, column=0, sticky="w")
        self.frames_sent_label = tk.Label(stats_grid, text="0", font=("Arial", 10))
        self.frames_sent_label.grid(row=0, column=1, padx=20)

        ###

        # Frame superior para estadísticas
        stats_frame = tk.LabelFrame(
            dashboard_frame, text="Estadísticas", font=("Arial", 12, "bold")
        )
        stats_frame.pack(fill="x", padx=10, pady=5)

        # Crear grid para estadísticas
        stats_grid = tk.Frame(stats_frame)
        stats_grid.pack(fill="x", padx=10, pady=10)

        # Tramas enviadas
        tk.Label(stats_grid, text="Tramas Enviadas:", font=("Arial", 10, "bold")).grid(
            row=0, column=0, sticky="w"
        )
        self.frames_sent_label = tk.Label(stats_grid, text=f"{self.frames_sent}", font=("Arial", 10))
        self.frames_sent_label.grid(row=0, column=1, padx=20)

        # Tramas recibidas
        tk.Label(stats_grid, text="Tramas Recibidas:", font=("Arial", 10, "bold")).grid(
            row=0, column=2, sticky="w"
        )
        self.frames_received_label = tk.Label(stats_grid, text=f"{self.frames_received}", font=("Arial", 10))
        self.frames_received_label.grid(row=0, column=3, padx=20)

        # Evento más común
        tk.Label(
            stats_grid, text="Evento Más Común (24h):", font=("Arial", 10, "bold")
        ).grid(row=1, column=0, sticky="w")
        self.most_common_event_label = tk.Label(
            stats_grid, text="N/A", font=("Arial", 10)
        )
        self.most_common_event_label.grid(
            row=1, column=1, columnspan=3, padx=20, sticky="w"
        )

        # Lista de eventos recientes
        events_frame = tk.LabelFrame(
            dashboard_frame, text="Eventos Recientes", font=("Arial", 12, "bold")
        )
        events_frame.pack(fill="x", padx=10, pady=5)

        self.events_listbox = tk.Listbox(events_frame, height=6)
        events_scrollbar = tk.Scrollbar(events_frame)
        events_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.events_listbox.pack(fill="x", padx=10, pady=5)
        self.events_listbox.config(yscrollcommand=events_scrollbar.set)
        events_scrollbar.config(command=self.events_listbox.yview)

    def create_commands_tab(self):
        """Crea la pestaña de comandos con scroll"""
        # Frame principal de la pestaña
        commands_tab = ttk.Frame(self.notebook)
        self.notebook.add(commands_tab, text="Comandos")

        # Detecta y carga las interfaces ethernet
        self.refresh_sensors_list()
        
        # Canvas con scrollbar
        canvas = tk.Canvas(commands_tab, borderwidth=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(commands_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")  # <-- GUARDA LA REFERENCIA
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Scroll con rueda del mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Formulario
        available_scrollable_frame = tk.LabelFrame(
            scrollable_frame, text="Formulario para enviar comandos"
        )
        available_scrollable_frame.pack(fill="x", padx=10, pady=5)

        form_frame = tk.LabelFrame(scrollable_frame, text="Formulario")
        form_frame.pack(fill="x", padx=10, pady=5)

        # Container principal del formulario
        form_container = tk.Frame(form_frame)
        form_container.pack(fill="x", padx=10, pady=10)

        # Fila 0: select de micro controlador
        mc_row = tk.Frame(form_container)
        mc_row.pack(fill="x", pady=5)

        tk.Label(
            mc_row,
            text="Micro Controlador:",
            font=("Arial", 10, "bold"),
            width=20,
            anchor="w",
        ).pack(side="left")
        self.mc_var = tk.StringVar()
        mc_combo = ttk.Combobox(
            mc_row,
            textvariable=self.mc_var,
            values=list(self.mc_available.keys()),
            state="readonly",
            width=30,
        )
        mc_combo.pack(side="left", padx=(10, 0))
        mc_combo.set("Seleccione un comando...")  # Valor por defecto

        # Fila 1: Input de MAC microcontrolador 
        destiny_row = tk.Frame(form_container)
        destiny_row.pack(fill="x", pady=5)

        tk.Label(
            destiny_row,
            text="MAC MC Destino:",
            font=("Arial", 10, "bold"),
            width=20,
            anchor="w",
        ).pack(side="left")
        self.mac_destino_var = tk.StringVar()
        mac_destino_entry = tk.Entry(destiny_row, textvariable=self.mac_destino_var, width=30)
        mac_destino_entry.pack(side="left", padx=(10, 0))

        # Fila 2: Select de comando
        command_row = tk.Frame(form_container)
        command_row.pack(fill="x", pady=5)

        tk.Label(
            command_row,
            text="Tipo de Comando:",
            font=("Arial", 10, "bold"),
            width=20,
            anchor="w",
        ).pack(side="left")
        self.command_var = tk.StringVar()
        command_combo = ttk.Combobox(
            command_row,
            textvariable=self.command_var,
            values=list(self.commands.keys()),
            state="readonly",
            width=30,
        )
        command_combo.pack(side="left", padx=(10, 0))
        command_combo.set("Seleccione un comando...")  # Valor por defecto

        # Fila 3: Número de ejecuciones
        executions_row = tk.Frame(form_container)
        executions_row.pack(fill="x", pady=5)

        tk.Label(
            executions_row,
            text="N° de Ejecuciones:",
            font=("Arial", 10, "bold"),
            width=20,
            anchor="w",
        ).pack(side="left")

        # Spinbox para número de ejecuciones
        self.executions_var = tk.IntVar(value=1)
        executions_spinbox = tk.Spinbox(
            executions_row,
            from_=1,
            to=100,
            textvariable=self.executions_var,
            width=10,
            justify="center",
        )
        executions_spinbox.pack(side="left", padx=(10, 0))

        tk.Label(executions_row, text="(1-100)", fg="gray", font=("Arial", 8)).pack(
            side="left", padx=(5, 0)
        )

        # Fila 4: Intervalo de tiempo
        interval_row = tk.Frame(form_container)
        interval_row.pack(fill="x", pady=5)

        tk.Label(
            interval_row,
            text="Intervalo (segundos):",
            font=("Arial", 10, "bold"),
            width=20,
            anchor="w",
        ).pack(side="left")

        # Spinbox para intervalo de tiempo
        self.interval_var = tk.DoubleVar(value=1.0)
        interval_spinbox = tk.Spinbox(
            interval_row,
            from_=0.1,
            to=3600.0,
            increment=0.5,
            textvariable=self.interval_var,
            width=10,
            justify="center",
            format="%.1f",
        )
        interval_spinbox.pack(side="left", padx=(10, 0))

        tk.Label(
            interval_row, text="(0.1-3600.0 seg)", fg="gray", font=("Arial", 8)
        ).pack(side="left", padx=(5, 0))

        # Fila 5: Botón de envío
        button_row = tk.Frame(form_container)
        button_row.pack(fill="x", pady=15)

        # Centrar el botón
        button_container = tk.Frame(button_row)
        button_container.pack()

        send_form_btn = tk.Button(
            button_container,
            text="🚀 Enviar Comando",
            command=self.process_command_form,
            font=("Arial", 11, "bold"),
            bg="#2ecc71",
            fg="white",
            width=20,
            height=2,
            relief="raised",
            bd=2,
        )
        send_form_btn.pack()

        # # Información adicional
        # info_row = tk.Frame(form_container)
        # info_row.pack(fill="x", pady=(10, 0))

        # info_text = "💡 Seleccione Micro Controladores arriba, configure el comando y ejecute"
        # tk.Label(
        #     info_row, text=info_text, fg="gray", font=("Arial", 9, "italic")
        # ).pack()

        # Frame de respuestas del sistema
        response_frame = tk.LabelFrame(scrollable_frame, text="Respuestas del Sistema")
        response_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.response_text = scrolledtext.ScrolledText(response_frame, height=8)
        self.response_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Cargar Micro Controladores iniciales
        # self.refresh_sensors_list()

    def create_menu(self):
        """Crea el menú principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Exportar Datos", command=self.export_to_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)

        # Menú Conexión
        connection_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Conexión", menu=connection_menu)
        connection_menu.add_command(
            label="Conectar/Desconectar", command=print("Conectar/desconectar|")
        )
        connection_menu.add_command(
            label="Configurar Puerto", command=print("configurar Puerto")
        )

    def make_package(self, data):
        """"Crea el paquete a enviar que consiste en un header + payload"""
        package = ""
        required_keys = ["selected_mc", "selected_command", "num_executions", "time_interval"]

        if not all(key in data for key in required_keys):
            print("Error: Faltan datos para construir el paquete")
            return None
        
        
        return package

    def process_command_form(self):
        """
        Procesa el formulario de comandos con los datos ingresados

        Esta función debe ser implementada para:
        1. Validar los datos del formulario
        2. Obtener los Micro Controladores seleccionados
        3. Ejecutar el comando según los parámetros especificados
        4. Mostrar progreso/resultados al usuario
        """

        # Obtener datos del formulario
        selected_mc = self.mc_var.get()
        selected_command = self.command_var.get()
        num_executions = self.executions_var.get()
        time_interval = self.interval_var.get()

        # Validaciones
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

        # Mostrar información de lo que se va a ejecutar
        info_message = f"""
    Comando a ejecutar: {selected_command}
    Valor del comando: {command_value}
    Micro Controladores objetivo: {', '.join(selected_mc) if selected_mc else 'Comando general'}
    Número de ejecuciones: {num_executions}
    Intervalo entre ejecuciones: {time_interval} segundos
    Tiempo total estimado: {num_executions * time_interval:.1f} segundos
        """.strip()

        if messagebox.askyesno("Confirmar Ejecución", info_message):
            # Ejemplo de estructura:
            """
            try:
                self.execute_command_sequence(
                    command_value=command_value,
                    target_mc=selected_mc,
                    executions=num_executions,
                    interval=time_interval
                )
            except Exception as e:
                messagebox.showerror("Error", f"Error ejecutando comando: {str(e)}")
            """

            # Mstrar en el área de respuestas y imprimir en consola
            titulo = "FORMULARIO PROCESADO:\n"
            comando_enviado = f"Comando: {selected_command} valor: ({command_value})"
            interfaz_usada = f"{self.mc_available.get(selected_mc)}"
            mc_receptor = f"Micro Controladores: {selected_mc}"
            n_ejecuciones_y_interv = f"Ejecuciones: {num_executions}, Intervalo: {time_interval}s"
            print(titulo)
            print(comando_enviado)
            print(interfaz_usada)
            print(mc_receptor)
            print(n_ejecuciones_y_interv)

            ## Mostrar Salida en "Respuestas del sistema"
            #TODO agregar salida de eventos en dashboard
            self.add_response(f"FORMULARIO PROCESADO:")
            self.add_response(f"Comando: {selected_command} ({command_value})")
            self.add_response(f"Micro Controladores: {selected_mc}")
            self.add_response(
                f"Ejecuciones: {num_executions}, Intervalo: {time_interval}s"
            )
            self.add_response("─" * 50)

    def refresh_sensors_list(self):
        """Actualiza la lista de interfaces ethernet conectadas y sus MACs"""
        
        # Limpiar datos previos
        self.mc_available = {}
        
        interfaces = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        for iface_name, addrs in interfaces.items():
            # Filtros básicos
            if iface_name == 'lo':  # Loopback
                continue
            if any(iface_name.startswith(prefix) for prefix in ['vir', 'docker', 'br-', 'veth', 'vmnet', 'vboxnet']):
                continue
            if 'wl' in iface_name.lower() or 'wifi' in iface_name.lower():  # WiFi
                continue
                
            # Verificar que la interfaz esté UP
            if iface_name in stats and not stats[iface_name].isup:
                continue
            
            # Buscar MAC
            mac = None
            for addr in addrs:
                if getattr(addr, 'family', None) == psutil.AF_LINK or getattr(addr, 'family', None) == 17:
                    mac = addr.address
                    break
            
            # Solo agregar si tiene MAC y no es 00:00:00:00:00:00
            if mac and mac != '00:00:00:00:00:00':
                self.mc_available[mac] = iface_name
                display_text = f"{iface_name} (MAC: {mac})"
        
        print("Interfaces ethernet detectadas:")
        for mac, iface in self.mc_available.items():
            print(f"{iface}: {mac}")
    
    def create_menu(self):
        """Crea el menú principal"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Exportar Datos", command=self.export_to_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)

        # Menú Conexión
        connection_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Conexión", menu=connection_menu)
        connection_menu.add_command(
            label="Conectar/Desconectar", command=print("Conectar/desconectar|")
        )
        connection_menu.add_command(
            label="Configurar Puerto", command=print("configurar Puerto")
        )

    def add_response(self, response):
        """Añade una respuesta al área de texto"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.response_text.insert(tk.END, f"[{timestamp}] {response}\n")
        self.response_text.see(tk.END)

    def update_interface(self):
        """Actualiza la interfaz periódicamente"""
        # Procesar datos en cola
        while not self.data_queue.empty():
            try:
                data = self.data_queue.get_nowait()
                self.process_sensor_data(data)
            except queue.Empty:
                break

        # Actualizar estadísticas
        self.frames_received_label.config(text=str(self.frames_received))
        self.update_most_common_event()

        # Programar siguiente actualización
        if self.running:
            self.root.after(1000, self.update_interface)

    def save_current_data(self):
        """Guarda los datos actuales en la base de datos"""
        if not self.sensor_data:
            messagebox.showinfo("Sin Datos", "No hay datos para guardar")
            return

        try:
            cursor = self.conn.cursor()
            saved_count = 0

            for data in self.sensor_data:
                cursor.execute(
                    """
                    INSERT INTO sensor_readings 
                    (timestamp, sensor_type, sensor_id, value, unit, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        data.get("timestamp", datetime.now().isoformat()),
                        data.get("type", "unknown"),
                        data.get("sensor_id", "unknown"),
                        data.get("value", 0),
                        data.get("unit", ""),
                        json.dumps(data),
                    ),
                )
                saved_count += 1

            self.conn.commit()
            messagebox.showinfo(
                "Guardado Exitoso",
                f"Se guardaron {saved_count} registros en la base de datos",
            )

            # Actualizar estadísticas y vista
            self.update_db_stats()
            self.load_recent_records()

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar datos: {str(e)}")

    def export_to_csv(self):
        """Exporta datos a archivo CSV"""
        from tkinter import filedialog
        import csv

        if not self.sensor_data:
            messagebox.showinfo("Sin Datos", "No hay datos para exportar")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )

        if filename:
            try:
                with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                    fieldnames = ["timestamp", "sensor_id", "type", "value", "unit"]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                    writer.writeheader()
                    for data in self.sensor_data:
                        writer.writerow(
                            {
                                "timestamp": data.get("timestamp", ""),
                                "sensor_id": data.get("sensor_id", ""),
                                "type": data.get("type", ""),
                                "value": data.get("value", ""),
                                "unit": data.get("unit", ""),
                            }
                        )

                messagebox.showinfo(
                    "Exportación Exitosa", f"Datos exportados a {filename}"
                )

            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar datos: {str(e)}")

    def clear_database(self):
        """Limpia la base de datos"""
        if messagebox.askyesno(
            "Confirmar", "¿Está seguro de que desea limpiar toda la base de datos?"
        ):
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM sensor_readings")
                cursor.execute("DELETE FROM communication_log")
                self.conn.commit()

                messagebox.showinfo(
                    "Base de Datos Limpiada", "Todos los registros han sido eliminados"
                )

                # Actualizar vistas
                self.update_db_stats()
                self.load_recent_records()

            except Exception as e:
                messagebox.showerror(
                    "Error", f"Error al limpiar base de datos: {str(e)}"
                )

    def update_db_stats(self):
        """Actualiza las estadísticas de la base de datos"""
        try:
            cursor = self.conn.cursor()

            # Contar registros totales
            cursor.execute("SELECT COUNT(*) FROM sensor_readings")
            total_records = cursor.fetchone()[0]

            # Contar por tipo de sensor
            cursor.execute(
                "SELECT sensor_type, COUNT(*) FROM sensor_readings GROUP BY sensor_type"
            )
            type_counts = cursor.fetchall()

            # Último registro
            cursor.execute(
                "SELECT timestamp FROM sensor_readings ORDER BY timestamp DESC LIMIT 1"
            )
            last_record = cursor.fetchone()
            last_time = last_record[0] if last_record else "N/A"

            # Actualizar texto de estadísticas
            stats_text = f"Registros totales: {total_records}\n"
            stats_text += f"Último registro: {last_time}\n\n"
            stats_text += "Registros por tipo de sensor:\n"

            for sensor_type, count in type_counts:
                stats_text += f"  {sensor_type}: {count} registros\n"

            self.db_stats_text.config(state="normal")
            self.db_stats_text.delete(1.0, tk.END)
            self.db_stats_text.insert(1.0, stats_text)
            self.db_stats_text.config(state="disabled")

        except Exception as e:
            print(f"Error actualizando estadísticas: {e}")

def main():
    """Función principal para ejecutar la aplicación"""
    root = tk.Tk()
    app = McControlApp(root)

    def on_closing():
        """Maneja el cierre de la aplicación"""
        app.running = False
        if app.serial_connection and app.serial_connection.is_open:
            app.serial_connection.close()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
