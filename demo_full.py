import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sqlite3
import serial
import json
import threading
import time
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict, deque
import queue

class SensorControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Control de Microcontroladores y Sensores")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Variables de estado
        self.logged_in = False
        self.serial_connection = None
        self.data_queue = queue.Queue()
        self.running = False
        
        # Contadores y estadísticas
        self.frames_sent = 0
        self.frames_received = 0
        self.sensor_data = deque(maxlen=1000)  # Últimos 1000 registros
        self.event_types = defaultdict(int)
        
        # Inicializar base de datos
        self.init_database()
        
        # Crear interfaz
        self.create_login_screen()
        
    def init_database(self):
        """Inicializa la base de datos SQLite"""
        self.conn = sqlite3.connect('sensor_data.db', check_same_thread=False)
        cursor = self.conn.cursor()
        
        # Tabla para datos de sensores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                sensor_type TEXT,
                sensor_id TEXT,
                value REAL,
                unit TEXT,
                metadata TEXT
            )
        ''')
        
        # Tabla para comunicación
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS communication_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                direction TEXT,
                data TEXT,
                frame_type TEXT
            )
        ''')
        
        self.conn.commit()
    
    def create_login_screen(self):
        """Crea la pantalla de login"""
        self.login_frame = tk.Frame(self.root, bg="#2c3e50", width=400, height=300)
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        # Título
        title_label = tk.Label(self.login_frame, text="Sistema de Control de Sensores", 
                              font=("Arial", 16, "bold"), fg="white", bg="#2c3e50")
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
        login_btn = tk.Button(self.login_frame, text="Iniciar Sesión", 
                             command=self.login, bg="#3498db", fg="white",
                             width=15, height=1)
        login_btn.pack(pady=20)
        
        # Enfocar en el campo de usuario
        self.username_entry.focus()
        
        # Bind Enter key
        self.root.bind('<Return>', lambda event: self.login())
    
    def login(self):
        """Verifica credenciales y accede a la aplicación"""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        # Credenciales hardcodeadas (solo para desarrollo)
        if username == "admin" and password == "sensor123":
            self.logged_in = True
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
        self.create_metadata_tab()
        self.create_traffic_tab()
        self.create_database_tab()
        
        # Barra de estado
        self.status_bar = tk.Label(self.root, text="Desconectado", 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Menú
        self.create_menu()
        
        # Iniciar hilo de comunicación
        self.start_communication_thread()
    
    def create_dashboard_tab(self):
        """Crea la pestaña del dashboard"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")
        
        # Frame superior para estadísticas
        stats_frame = tk.LabelFrame(dashboard_frame, text="Estadísticas", 
                                   font=("Arial", 12, "bold"))
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        # Crear grid para estadísticas
        stats_grid = tk.Frame(stats_frame)
        stats_grid.pack(fill="x", padx=10, pady=10)
        
        # Tramas enviadas
        tk.Label(stats_grid, text="Tramas Enviadas:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.frames_sent_label = tk.Label(stats_grid, text="0", font=("Arial", 10))
        self.frames_sent_label.grid(row=0, column=1, padx=20)
        
        # Tramas recibidas
        tk.Label(stats_grid, text="Tramas Recibidas:", font=("Arial", 10, "bold")).grid(row=0, column=2, sticky="w")
        self.frames_received_label = tk.Label(stats_grid, text="0", font=("Arial", 10))
        self.frames_received_label.grid(row=0, column=3, padx=20)
        
        # Evento más común
        tk.Label(stats_grid, text="Evento Más Común (24h):", font=("Arial", 10, "bold")).grid(row=1, column=0, sticky="w")
        self.most_common_event_label = tk.Label(stats_grid, text="N/A", font=("Arial", 10))
        self.most_common_event_label.grid(row=1, column=1, columnspan=3, padx=20, sticky="w")
        
        # Frame para gráficos
        charts_frame = tk.LabelFrame(dashboard_frame, text="Monitoreo en Tiempo Real", 
                                    font=("Arial", 12, "bold"))
        charts_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Crear gráfico de temperatura
        self.create_temperature_chart(charts_frame)
        
        # Lista de eventos recientes
        events_frame = tk.LabelFrame(dashboard_frame, text="Eventos Recientes", 
                                    font=("Arial", 12, "bold"))
        events_frame.pack(fill="x", padx=10, pady=5)
        
        self.events_listbox = tk.Listbox(events_frame, height=6)
        events_scrollbar = tk.Scrollbar(events_frame)
        events_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.events_listbox.pack(fill="x", padx=10, pady=5)
        self.events_listbox.config(yscrollcommand=events_scrollbar.set)
        events_scrollbar.config(command=self.events_listbox.yview)
    
    def create_temperature_chart(self, parent):
        """Crea el gráfico de temperatura"""
        self.temp_fig, self.temp_ax = plt.subplots(figsize=(8, 4))
        self.temp_ax.set_title("Temperatura en Tiempo Real")
        self.temp_ax.set_xlabel("Tiempo")
        self.temp_ax.set_ylabel("Temperatura (°C)")
        self.temp_ax.grid(True)
        
        self.temp_canvas = FigureCanvasTkAgg(self.temp_fig, parent)
        self.temp_canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)
    
    def create_commands_tab(self):
        """Crea la pestaña de comandos"""
        commands_frame = ttk.Frame(self.notebook)
        self.notebook.add(commands_frame, text="Comandos")
        
        # Frame de conexión
        connection_frame = tk.LabelFrame(commands_frame, text="Configuración de Conexión")
        connection_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(connection_frame, text="Puerto Serial:").grid(row=0, column=0, padx=5, pady=5)
        self.port_entry = tk.Entry(connection_frame, width=15)
        self.port_entry.insert(0, "COM3")  # Puerto por defecto
        self.port_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(connection_frame, text="Baudios:").grid(row=0, column=2, padx=5, pady=5)
        self.baud_var = tk.StringVar(value="9600")
        baud_combo = ttk.Combobox(connection_frame, textvariable=self.baud_var, 
                                 values=["9600", "19200", "38400", "57600", "115200"])
        baud_combo.grid(row=0, column=3, padx=5, pady=5)
        
        self.connect_btn = tk.Button(connection_frame, text="Conectar", 
                                    command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=4, padx=10, pady=5)
        
        # Frame de comandos disponibles
        available_commands_frame = tk.LabelFrame(commands_frame, text="Comandos Disponibles")
        available_commands_frame.pack(fill="x", padx=10, pady=5)
        
        # Lista de comandos predefinidos
        self.commands = {
            "GET_TEMP": "Obtener temperatura",
            "GET_GAMMA": "Obtener datos gamma/PET",
            "START_MONITOR": "Iniciar monitoreo continuo",
            "STOP_MONITOR": "Detener monitoreo",
            "GET_STATUS": "Obtener estado del sistema",
            "RESET": "Reiniciar microcontrolador",
            "CALIBRATE": "Calibrar sensores"
        }
        
        # Crear botones para cada comando
        cmd_row = 0
        cmd_col = 0
        for cmd, description in self.commands.items():
            btn = tk.Button(available_commands_frame, text=f"{cmd}\n({description})",
                           command=lambda c=cmd: self.send_command(c),
                           width=15, height=3)
            btn.grid(row=cmd_row, column=cmd_col, padx=5, pady=5)
            cmd_col += 1
            if cmd_col > 2:
                cmd_col = 0
                cmd_row += 1
        
        # Frame de comando personalizado
        custom_frame = tk.LabelFrame(commands_frame, text="Comando Personalizado")
        custom_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(custom_frame, text="Comando:").pack(anchor="w", padx=5)
        self.custom_command_entry = tk.Entry(custom_frame, width=50)
        self.custom_command_entry.pack(fill="x", padx=5, pady=2)
        
        send_custom_btn = tk.Button(custom_frame, text="Enviar Comando Personalizado",
                                   command=self.send_custom_command)
        send_custom_btn.pack(pady=5)
        
        # Frame de respuestas
        response_frame = tk.LabelFrame(commands_frame, text="Respuestas del Sistema")
        response_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.response_text = scrolledtext.ScrolledText(response_frame, height=10)
        self.response_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def create_metadata_tab(self):
        """Crea la pestaña de metadatos"""
        metadata_frame = ttk.Frame(self.notebook)
        self.notebook.add(metadata_frame, text="Metadatos")
        
        # Información del microcontrolador
        mcu_frame = tk.LabelFrame(metadata_frame, text="Información del Microcontrolador")
        mcu_frame.pack(fill="x", padx=10, pady=5)
        
        mcu_info = tk.Text(mcu_frame, height=8, state="disabled")
        mcu_info.pack(fill="x", padx=10, pady=5)
        
        # Información de sensores
        sensors_frame = tk.LabelFrame(metadata_frame, text="Sensores Conectados")
        sensors_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Treeview para mostrar sensores
        columns = ("ID", "Tipo", "Estado", "Última Lectura", "Unidad")
        self.sensors_tree = ttk.Treeview(sensors_frame, columns=columns, show="headings")
        
        for col in columns:
            self.sensors_tree.heading(col, text=col)
            self.sensors_tree.column(col, width=120)
        
        sensors_scrollbar = ttk.Scrollbar(sensors_frame, orient="vertical", 
                                         command=self.sensors_tree.yview)
        self.sensors_tree.configure(yscrollcommand=sensors_scrollbar.set)
        
        self.sensors_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        sensors_scrollbar.pack(side="right", fill="y")
        
        # Datos de ejemplo
        self.update_sensors_metadata()
    
    def create_traffic_tab(self):
        """Crea la pestaña de tráfico de datos gamma"""
        traffic_frame = ttk.Frame(self.notebook)
        self.notebook.add(traffic_frame, text="Tráfico Gamma/PET")
        
        # Controles superiores
        controls_frame = tk.Frame(traffic_frame)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        tk.Label(controls_frame, text="Filtrar por:").pack(side="left")
        
        self.filter_var = tk.StringVar(value="Todos")
        filter_combo = ttk.Combobox(controls_frame, textvariable=self.filter_var,
                                   values=["Todos", "Gamma", "PET", "Temperatura"])
        filter_combo.pack(side="left", padx=5)
        
        filter_btn = tk.Button(controls_frame, text="Aplicar Filtro",
                              command=self.apply_traffic_filter)
        filter_btn.pack(side="left", padx=5)
        
        refresh_btn = tk.Button(controls_frame, text="Actualizar",
                               command=self.refresh_traffic_data)
        refresh_btn.pack(side="left", padx=5)
        
        # Tabla de tráfico de datos
        traffic_columns = ("Timestamp", "Sensor", "Tipo", "Valor", "Unidad", "Calidad")
        self.traffic_tree = ttk.Treeview(traffic_frame, columns=traffic_columns, show="headings")
        
        for col in traffic_columns:
            self.traffic_tree.heading(col, text=col)
            self.traffic_tree.column(col, width=100)
        
        traffic_scrollbar = ttk.Scrollbar(traffic_frame, orient="vertical",
                                         command=self.traffic_tree.yview)
        self.traffic_tree.configure(yscrollcommand=traffic_scrollbar.set)
        
        self.traffic_tree.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        traffic_scrollbar.pack(side="right", fill="y")
        
        # Cargar datos iniciales
        self.refresh_traffic_data()
    
    def create_database_tab(self):
        """Crea la pestaña de gestión de base de datos"""
        db_frame = ttk.Frame(self.notebook)
        self.notebook.add(db_frame, text="Base de Datos")
        
        # Controles de base de datos
        controls_frame = tk.LabelFrame(db_frame, text="Gestión de Datos")
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        save_btn = tk.Button(controls_frame, text="Guardar Datos Actuales",
                            command=self.save_current_data)
        save_btn.pack(side="left", padx=5, pady=5)
        
        export_btn = tk.Button(controls_frame, text="Exportar a CSV",
                              command=self.export_to_csv)
        export_btn.pack(side="left", padx=5, pady=5)
        
        clear_btn = tk.Button(controls_frame, text="Limpiar Base de Datos",
                             command=self.clear_database)
        clear_btn.pack(side="left", padx=5, pady=5)
        
        # Estadísticas de la base de datos
        stats_frame = tk.LabelFrame(db_frame, text="Estadísticas")
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        self.db_stats_text = tk.Text(stats_frame, height=5, state="disabled")
        self.db_stats_text.pack(fill="x", padx=10, pady=5)
        
        # Vista de registros recientes
        recent_frame = tk.LabelFrame(db_frame, text="Registros Recientes")
        recent_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        db_columns = ("ID", "Timestamp", "Sensor", "Valor", "Unidad")
        self.db_tree = ttk.Treeview(recent_frame, columns=db_columns, show="headings")
        
        for col in db_columns:
            self.db_tree.heading(col, text=col)
            self.db_tree.column(col, width=100)
        
        db_scrollbar = ttk.Scrollbar(recent_frame, orient="vertical",
                                    command=self.db_tree.yview)
        self.db_tree.configure(yscrollcommand=db_scrollbar.set)
        
        self.db_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        db_scrollbar.pack(side="right", fill="y")
        
        self.update_db_stats()
        self.load_recent_records()
    
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
        connection_menu.add_command(label="Conectar/Desconectar", 
                                   command=self.toggle_connection)
        connection_menu.add_command(label="Configurar Puerto", 
                                   command=self.configure_port)
    
    def toggle_connection(self):
        """Conecta o desconecta el puerto serial"""
        if self.serial_connection and self.serial_connection.is_open:
            self.disconnect_serial()
        else:
            self.connect_serial()
    
    def connect_serial(self):
        """Conecta al puerto serial"""
        try:
            port = self.port_entry.get()
            baud = int(self.baud_var.get())
            
            self.serial_connection = serial.Serial(port, baud, timeout=1)
            self.status_bar.config(text=f"Conectado a {port} @ {baud} bps")
            self.connect_btn.config(text="Desconectar")
            
            messagebox.showinfo("Conexión", f"Conectado exitosamente a {port}")
            
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar: {str(e)}")
    
    def disconnect_serial(self):
        """Desconecta el puerto serial"""
        if self.serial_connection:
            self.serial_connection.close()
            self.serial_connection = None
            self.status_bar.config(text="Desconectado")
            self.connect_btn.config(text="Conectar")
            messagebox.showinfo("Conexión", "Desconectado exitosamente")
    
    def send_command(self, command):
        """Envía un comando predefinido"""
        if not self.serial_connection or not self.serial_connection.is_open:
            messagebox.showwarning("Sin Conexión", "Debe conectarse al puerto serial primero")
            return
        
        try:
            command_str = f"{command}\n"
            self.serial_connection.write(command_str.encode())
            self.frames_sent += 1
            self.frames_sent_label.config(text=str(self.frames_sent))
            
            # Log del comando enviado
            self.log_communication("SENT", command, "COMMAND")
            self.add_response(f"Comando enviado: {command}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al enviar comando: {str(e)}")
    
    def send_custom_command(self):
        """Envía un comando personalizado"""
        command = self.custom_command_entry.get()
        if command:
            self.send_command(command)
            self.custom_command_entry.delete(0, tk.END)
    
    def add_response(self, response):
        """Añade una respuesta al área de texto"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.response_text.insert(tk.END, f"[{timestamp}] {response}\n")
        self.response_text.see(tk.END)
    
    def start_communication_thread(self):
        """Inicia el hilo de comunicación para recibir datos"""
        self.running = True
        self.comm_thread = threading.Thread(target=self.communication_loop, daemon=True)
        self.comm_thread.start()
        
        # Actualizar interfaz periódicamente
        self.root.after(1000, self.update_interface)
    
    def communication_loop(self):
        """Bucle principal de comunicación"""
        while self.running:
            # Simular recepción de datos (reemplazar con lectura serial real)
            if self.serial_connection and self.serial_connection.is_open:
                try:
                    if self.serial_connection.in_waiting > 0:
                        data = self.serial_connection.readline().decode().strip()
                        if data:
                            self.process_received_data(data)
                except:
                    pass
            else:
                # Simular datos para pruebas
                self.simulate_sensor_data()
            
            time.sleep(1)
    
    def simulate_sensor_data(self):
        """Simula datos de sensores para pruebas"""
        import random
        
        # Simular datos de temperatura
        temp_data = {
            'sensor_id': 'TEMP_001',
            'type': 'temperature',
            'value': round(random.uniform(20.0, 35.0), 2),
            'unit': '°C',
            'timestamp': datetime.now().isoformat()
        }
        
        # Simular datos gamma
        gamma_data = {
            'sensor_id': 'GAMMA_001',
            'type': 'gamma',
            'value': round(random.uniform(0.1, 2.5), 3),
            'unit': 'μSv/h',
            'timestamp': datetime.now().isoformat()
        }
        
        # Procesar datos simulados
        for data in [temp_data, gamma_data]:
            self.data_queue.put(data)
    
    def process_received_data(self, data):
        """Procesa los datos recibidos del microcontrolador"""
        try:
            # Intentar parsear como JSON
            sensor_data = json.loads(data)
            self.data_queue.put(sensor_data)
            
        except json.JSONDecodeError:
            # Si no es JSON, tratar como texto plano
            self.add_response(f"Datos recibidos: {data}")
        
        self.frames_received += 1
        self.log_communication("RECEIVED", data, "DATA")
    
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
    
    def process_sensor_data(self, data):
        """Procesa y almacena los datos del sensor"""
        self.sensor_data.append(data)
        
        # Actualizar tipos de eventos
        event_type = data.get('type', 'unknown')
        self.event_types[event_type] += 1
        
        # Añadir a lista de eventos
        timestamp = data.get('timestamp', datetime.now().isoformat())
        event_text = f"{timestamp[:19]} - {event_type.upper()}: {data.get('value')} {data.get('unit', '')}"
        self.events_listbox.insert(0, event_text)
        
        # Mantener solo los últimos 50 eventos
        if self.events_listbox.size() > 50:
            self.events_listbox.delete(tk.END)
        
        # Actualizar gráfico si es temperatura
        if event_type == 'temperature':
            self.update_temperature_chart(data)
    
    def update_temperature_chart(self, data):
        """Actualiza el gráfico de temperatura"""
        try:
            if not hasattr(self, 'temp_times'):
                self.temp_times = deque(maxlen=50)
                self.temp_values = deque(maxlen=50)
            
            self.temp_times.append(datetime.now())
            self.temp_values.append(float(data.get('value', 0)))
            
            self.temp_ax.clear()
            self.temp_ax.plot(self.temp_times, self.temp_values, 'b-o', markersize=4)
            self.temp_ax.set_title("Temperatura en Tiempo Real")
            self.temp_ax.set_xlabel("Tiempo")
            self.temp_ax.set_ylabel("Temperatura (°C)")
            self.temp_ax.grid(True)
            
            # Formatear eje X
            if len(self.temp_times) > 1:
                self.temp_fig.autofmt_xdate()
            
            self.temp_canvas.draw()
            
        except Exception as e:
            print(f"Error actualizando gráfico: {e}")
    
    def update_most_common_event(self):
        """Actualiza el evento más común en las últimas 24h"""
        if self.event_types:
            most_common = max(self.event_types, key=self.event_types.get)
            count = self.event_types[most_common]
            self.most_common_event_label.config(text=f"{most_common} ({count} eventos)")
        else:
            self.most_common_event_label.config(text="N/A")
    
    def update_sensors_metadata(self):
        """Actualiza la información de metadatos de sensores"""
        # Limpiar datos existentes
        for item in self.sensors_tree.get_children():
            self.sensors_tree.delete(item)
        
        # Datos de ejemplo
        sensors_info = [
            ("TEMP_001", "Temperatura", "Activo", "25.3°C", "°C"),
            ("TEMP_002", "Temperatura", "Activo", "24.8°C", "°C"),
            ("GAMMA_001", "Gamma", "Activo", "0.125", "μSv/h"),
            ("PET_001", "PET Scanner", "Activo", "Normal", "Status"),
        ]
        
        for sensor_info in sensors_info:
            self.sensors_tree.insert("", "end", values=sensor_info)
    
    def apply_traffic_filter(self):
        """Aplica filtros al tráfico de datos"""
        filter_type = self.filter_var.get()
        
        # Limpiar tabla actual
        for item in self.traffic_tree.get_children():
            self.traffic_tree.delete(item)
        
        # Filtrar datos según selección
        filtered_data = []
        for data in self.sensor_data:
            if filter_type == "Todos" or data.get('type', '').lower() == filter_type.lower():
                filtered_data.append(data)
        
        # Mostrar datos filtrados
        for data in filtered_data[-100:]:  # Últimos 100 registros
            timestamp = data.get('timestamp', '')[:19]  # Solo fecha y hora
            sensor_id = data.get('sensor_id', 'N/A')
            sensor_type = data.get('type', 'N/A').capitalize()
            value = data.get('value', 'N/A')
            unit = data.get('unit', '')
            quality = "Buena"  # Simular calidad de datos
            
            self.traffic_tree.insert("", "end", values=(timestamp, sensor_id, sensor_type, value, unit, quality))
    
    def refresh_traffic_data(self):
        """Actualiza los datos de tráfico"""
        self.apply_traffic_filter()
    
    def save_current_data(self):
        """Guarda los datos actuales en la base de datos"""
        if not self.sensor_data:
            messagebox.showinfo("Sin Datos", "No hay datos para guardar")
            return
        
        try:
            cursor = self.conn.cursor()
            saved_count = 0
            
            for data in self.sensor_data:
                cursor.execute('''
                    INSERT INTO sensor_readings 
                    (timestamp, sensor_type, sensor_id, value, unit, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('timestamp', datetime.now().isoformat()),
                    data.get('type', 'unknown'),
                    data.get('sensor_id', 'unknown'),
                    data.get('value', 0),
                    data.get('unit', ''),
                    json.dumps(data)
                ))
                saved_count += 1
            
            self.conn.commit()
            messagebox.showinfo("Guardado Exitoso", f"Se guardaron {saved_count} registros en la base de datos")
            
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
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = ['timestamp', 'sensor_id', 'type', 'value', 'unit']
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for data in self.sensor_data:
                        writer.writerow({
                            'timestamp': data.get('timestamp', ''),
                            'sensor_id': data.get('sensor_id', ''),
                            'type': data.get('type', ''),
                            'value': data.get('value', ''),
                            'unit': data.get('unit', '')
                        })
                
                messagebox.showinfo("Exportación Exitosa", f"Datos exportados a {filename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar datos: {str(e)}")
    
    def clear_database(self):
        """Limpia la base de datos"""
        if messagebox.askyesno("Confirmar", "¿Está seguro de que desea limpiar toda la base de datos?"):
            try:
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM sensor_readings")
                cursor.execute("DELETE FROM communication_log")
                self.conn.commit()
                
                messagebox.showinfo("Base de Datos Limpiada", "Todos los registros han sido eliminados")
                
                # Actualizar vistas
                self.update_db_stats()
                self.load_recent_records()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al limpiar base de datos: {str(e)}")
    
    def update_db_stats(self):
        """Actualiza las estadísticas de la base de datos"""
        try:
            cursor = self.conn.cursor()
            
            # Contar registros totales
            cursor.execute("SELECT COUNT(*) FROM sensor_readings")
            total_records = cursor.fetchone()[0]
            
            # Contar por tipo de sensor
            cursor.execute("SELECT sensor_type, COUNT(*) FROM sensor_readings GROUP BY sensor_type")
            type_counts = cursor.fetchall()
            
            # Último registro
            cursor.execute("SELECT timestamp FROM sensor_readings ORDER BY timestamp DESC LIMIT 1")
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
    
    def load_recent_records(self):
        """Carga los registros más recientes de la base de datos"""
        try:
            # Limpiar tabla actual
            for item in self.db_tree.get_children():
                self.db_tree.delete(item)
            
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT id, timestamp, sensor_type, value, unit
                FROM sensor_readings
                ORDER BY timestamp DESC
                LIMIT 100
            ''')
            
            records = cursor.fetchall()
            
            for record in records:
                # Formatear timestamp
                timestamp = record[1][:19] if record[1] else "N/A"
                
                self.db_tree.insert("", "end", values=(
                    record[0],  # ID
                    timestamp,  # Timestamp
                    record[2],  # Sensor type
                    record[3],  # Value
                    record[4]   # Unit
                ))
                
        except Exception as e:
            print(f"Error cargando registros: {e}")
    
    def log_communication(self, direction, data, frame_type):
        """Registra la comunicación en la base de datos"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO communication_log (timestamp, direction, data, frame_type)
                VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                direction,
                str(data),
                frame_type
            ))
            self.conn.commit()
            
        except Exception as e:
            print(f"Error registrando comunicación: {e}")
    
    def configure_port(self):
        """Abre una ventana de configuración del puerto"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Configuración de Puerto")
        config_window.geometry("400x300")
        config_window.resizable(False, False)
        
        # Puerto
        tk.Label(config_window, text="Puerto Serial:", font=("Arial", 10, "bold")).pack(pady=5)
        port_frame = tk.Frame(config_window)
        port_frame.pack(pady=5)
        
        port_entry = tk.Entry(port_frame, width=20)
        port_entry.insert(0, self.port_entry.get())
        port_entry.pack(side="left", padx=5)
        
        # Baudios
        tk.Label(config_window, text="Velocidad (Baudios):", font=("Arial", 10, "bold")).pack(pady=5)
        baud_frame = tk.Frame(config_window)
        baud_frame.pack(pady=5)
        
        baud_var = tk.StringVar(value=self.baud_var.get())
        baud_combo = ttk.Combobox(baud_frame, textvariable=baud_var,
                                 values=["1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"])
        baud_combo.pack(padx=5)
        
        # Configuraciones adicionales
        tk.Label(config_window, text="Configuraciones Adicionales:", font=("Arial", 10, "bold")).pack(pady=(20,5))
        
        # Timeout
        timeout_frame = tk.Frame(config_window)
        timeout_frame.pack(pady=2)
        tk.Label(timeout_frame, text="Timeout (segundos):").pack(side="left")
        timeout_entry = tk.Entry(timeout_frame, width=10)
        timeout_entry.insert(0, "1")
        timeout_entry.pack(side="right", padx=5)
        
        # Bits de datos
        databits_frame = tk.Frame(config_window)
        databits_frame.pack(pady=2)
        tk.Label(databits_frame, text="Bits de datos:").pack(side="left")
        databits_var = tk.StringVar(value="8")
        databits_combo = ttk.Combobox(databits_frame, textvariable=databits_var,
                                     values=["5", "6", "7", "8"], width=5)
        databits_combo.pack(side="right", padx=5)
        
        # Paridad
        parity_frame = tk.Frame(config_window)
        parity_frame.pack(pady=2)
        tk.Label(parity_frame, text="Paridad:").pack(side="left")
        parity_var = tk.StringVar(value="None")
        parity_combo = ttk.Combobox(parity_frame, textvariable=parity_var,
                                   values=["None", "Even", "Odd"], width=8)
        parity_combo.pack(side="right", padx=5)
        
        # Botones
        button_frame = tk.Frame(config_window)
        button_frame.pack(pady=20)
        
        def apply_config():
            self.port_entry.delete(0, tk.END)
            self.port_entry.insert(0, port_entry.get())
            self.baud_var.set(baud_var.get())
            config_window.destroy()
            messagebox.showinfo("Configuración", "Configuración aplicada correctamente")
        
        apply_btn = tk.Button(button_frame, text="Aplicar", command=apply_config)
        apply_btn.pack(side="left", padx=5)
        
        cancel_btn = tk.Button(button_frame, text="Cancelar", command=config_window.destroy)
        cancel_btn.pack(side="left", padx=5)
    
    def __del__(self):
        """Destructor para cerrar conexiones"""
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        if hasattr(self, 'conn'):
            self.conn.close()


def main():
    """Función principal para ejecutar la aplicación"""
    root = tk.Tk()
    app = SensorControlApp(root)
    
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