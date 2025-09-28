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
        self.admin_in = False
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
        self.create_main_interface()
        
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
        # self.create_metadata_tab()
        # self.create_traffic_tab()
        # self.create_database_tab()
        
        # Barra de estado
        self.status_bar = tk.Label(self.root, text="Desconectado", 
                                  bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Menú
        self.create_menu()
        

    def create_dashboard_tab(self):
        """Crea la pestaña del dashboard"""
        dashboard_frame = ttk.Frame(self.notebook)
        self.notebook.add(dashboard_frame, text="Dashboard")

        ### 
        # Frame superior para Gestionar Sensores
        stats_frame = tk.LabelFrame(dashboard_frame, text="Centro de Sensores", 
                                   font=("Arial", 12, "bold"))
        stats_frame.pack(fill="x", padx=10, pady=5)
        
        # Crear grid para gestor de sensores
        stats_grid = tk.Frame(stats_frame)
        stats_grid.pack(fill="x", padx=10, pady=10)

        # Tramas enviadas
        tk.Label(stats_grid, text="Sensores Registrados", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w")
        self.frames_sent_label = tk.Label(stats_grid, text="0", font=("Arial", 10))
        self.frames_sent_label.grid(row=0, column=1, padx=20)
        
        ###
        
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
    
    def create_commands_tab(self):
        """Crea la pestaña de comandos"""
        commands_frame = ttk.Frame(self.notebook)
        self.notebook.add(commands_frame, text="Comandos")
        
        # Frame de selección de sensores
        sensor_selection_frame = tk.LabelFrame(commands_frame, text="Seleccionar Sensores")
        sensor_selection_frame.pack(fill="both", expand=True, padx=10, pady=5)

         # Container para los dos listados
        listboxes_container = tk.Frame(sensor_selection_frame)
        listboxes_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Frame izquierdo - Sensores disponibles
        left_frame = tk.Frame(listboxes_container)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        tk.Label(left_frame, text="Sensores Disponibles", font=("Arial", 10, "bold")).pack()
        
        # Listbox de sensores disponibles
        self.available_sensors_listbox = tk.Listbox(left_frame, selectmode=tk.SINGLE, height=12)
        self.available_sensors_listbox.pack(fill="both", expand=True, pady=(5, 0))
        self.available_sensors_listbox.bind('<Double-Button-1>', self.move_to_selected)
        
        # Scrollbar para sensores disponibles
        available_scrollbar = tk.Scrollbar(left_frame, orient="vertical")
        available_scrollbar.pack(side="right", fill="y")
        self.available_sensors_listbox.config(yscrollcommand=available_scrollbar.set)
        available_scrollbar.config(command=self.available_sensors_listbox.yview)
        
        # Frame central - Botones de control
        control_frame = tk.Frame(listboxes_container, width=80)
        control_frame.pack(side="left", fill="y", padx=5)
        control_frame.pack_propagate(False)  # Mantener ancho fijo
        
        # Espaciador superior
        tk.Label(control_frame, text="").pack(pady=10)
        
        # Botón agregar seleccionado
        add_btn = tk.Button(control_frame, text="▶", font=("Arial", 12, "bold"),
                           command=self.move_to_selected, width=6, height=1)
        add_btn.pack(pady=5)
        
        # Botón quitar seleccionado
        remove_btn = tk.Button(control_frame, text="◀", font=("Arial", 12, "bold"),
                              command=self.move_to_available, width=6, height=1)
        remove_btn.pack(pady=5)
        
        # Separador
        tk.Label(control_frame, text="─────", fg="gray").pack(pady=10)
        
        # Botón seleccionar todos
        select_all_btn = tk.Button(control_frame, text="▶▶", font=("Arial", 10, "bold"),
                                  command=self.select_all_sensors, width=6, height=1)
        select_all_btn.pack(pady=2)
        
        # Botón deseleccionar todos
        deselect_all_btn = tk.Button(control_frame, text="◀◀", font=("Arial", 10, "bold"),
                                    command=self.deselect_all_sensors, width=6, height=1)
        deselect_all_btn.pack(pady=2)
        
        # Frame derecho - Sensores seleccionados
        right_frame = tk.Frame(listboxes_container)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        tk.Label(right_frame, text="Sensores Seleccionados", font=("Arial", 10, "bold")).pack()
        
        # Listbox de sensores seleccionados
        self.selected_sensors_listbox = tk.Listbox(right_frame, selectmode=tk.SINGLE, height=12)
        self.selected_sensors_listbox.pack(fill="both", expand=True, pady=(5, 0))
        self.selected_sensors_listbox.bind('<Double-Button-1>', self.move_to_available)
        
        # Scrollbar para sensores seleccionados
        selected_scrollbar = tk.Scrollbar(right_frame, orient="vertical")
        selected_scrollbar.pack(side="right", fill="y")
        self.selected_sensors_listbox.config(yscrollcommand=selected_scrollbar.set)
        selected_scrollbar.config(command=self.selected_sensors_listbox.yview)
        
        # Frame de información de selección
        info_frame = tk.Frame(sensor_selection_frame)
        info_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        self.selection_info_label = tk.Label(info_frame, text="0 sensores seleccionados", 
                                           font=("Arial", 9), fg="gray")
        self.selection_info_label.pack(side="left")
        
        refresh_sensors_btn = tk.Button(info_frame, text="🔄 Actualizar Lista", 
                                       command=self.refresh_sensors_list)
        refresh_sensors_btn.pack(side="right")
        
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
    
        
        # Frame de respuestas
        response_frame = tk.LabelFrame(commands_frame, text="Respuestas del Sistema")
        response_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.response_text = scrolledtext.ScrolledText(response_frame, height=10)
        self.response_text.pack(fill="both", expand=True, padx=5, pady=5)
    
    def refresh_sensors_list(self):
        """Actualiza la lista de sensores disponibles desde la base de datos"""
        try:
            # Limpiar listbox de disponibles
            self.available_sensors_listbox.delete(0, tk.END)
            
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT DISTINCT sensor_id, sensor_type 
                FROM sensor_readings 
                ORDER BY sensor_type, sensor_id
            ''')
            
            sensors_from_db = cursor.fetchall()
            
            # Si no hay sensores en la BD, agregar algunos de ejemplo
            if not sensors_from_db:
                example_sensors = [
                    ("TEMP_001", "temperature"),
                    ("TEMP_002", "temperature"),
                    ("GAMMA_001", "gamma"),
                    ("GAMMA_002", "gamma"),
                    ("PET_001", "pet_scanner"),
                    ("PRESSURE_001", "pressure"),
                    ("HUMIDITY_001", "humidity")
                ]
                
                # Agregar sensores de ejemplo a la lista
                for sensor_id, sensor_type in example_sensors:
                    display_text = f"{sensor_id} ({sensor_type.upper()})"
                    self.available_sensors_listbox.insert(tk.END, display_text)
            else:
                # Agregar sensores reales de la BD
                for sensor_id, sensor_type in sensors_from_db:
                    display_text = f"{sensor_id} ({sensor_type.upper()})"
                    # Solo agregar si no está ya en la lista de seleccionados
                    if not self._is_sensor_selected(display_text):
                        self.available_sensors_listbox.insert(tk.END, display_text)
            
            self.update_selection_info()
            
        except Exception as e:
            print(f"Error actualizando lista de sensores: {e}")
            # En caso de error, mostrar sensores de ejemplo
            example_sensors = [
                "TEMP_001 (TEMPERATURE)",
                "TEMP_002 (TEMPERATURE)", 
                "GAMMA_001 (GAMMA)",
                "PET_001 (PET_SCANNER)"
            ]
            
            self.available_sensors_listbox.delete(0, tk.END)
            for sensor in example_sensors:
                self.available_sensors_listbox.insert(tk.END, sensor)
    
    def _is_sensor_selected(self, sensor_text):
        """Verifica si un sensor ya está en la lista de seleccionados"""
        selected_items = self.selected_sensors_listbox.get(0, tk.END)
        return sensor_text in selected_items

    def move_to_selected(self, event=None):
        """Mueve el sensor seleccionado a la lista de seleccionados"""
        try:
            selection = self.available_sensors_listbox.curselection()
            if selection:
                index = selection[0]
                sensor_text = self.available_sensors_listbox.get(index)
                
                # Agregar a seleccionados
                self.selected_sensors_listbox.insert(tk.END, sensor_text)
                
                # Quitar de disponibles
                self.available_sensors_listbox.delete(index)
                
                self.update_selection_info()
                
        except Exception as e:
            print(f"Error moviendo sensor a seleccionados: {e}")
    
    def move_to_available(self, event=None):
        """Mueve el sensor seleccionado de vuelta a la lista de disponibles"""
        try:
            selection = self.selected_sensors_listbox.curselection()
            if selection:
                index = selection[0]
                sensor_text = self.selected_sensors_listbox.get(index)
                
                # Agregar a disponibles
                self.available_sensors_listbox.insert(tk.END, sensor_text)
                
                # Quitar de seleccionados
                self.selected_sensors_listbox.delete(index)
                
                self.update_selection_info()
                
        except Exception as e:
            print(f"Error moviendo sensor a disponibles: {e}")
    
    def select_all_sensors(self):
        """Selecciona todos los sensores disponibles"""
        try:
            # Mover todos los sensores de disponibles a seleccionados
            items = list(self.available_sensors_listbox.get(0, tk.END))
            
            for item in items:
                self.selected_sensors_listbox.insert(tk.END, item)
            
            # Limpiar lista de disponibles
            self.available_sensors_listbox.delete(0, tk.END)
            
            self.update_selection_info()
            
        except Exception as e:
            print(f"Error seleccionando todos los sensores: {e}")
    
    def deselect_all_sensors(self):
        """Deselecciona todos los sensores"""
        try:
            # Mover todos los sensores de seleccionados a disponibles
            items = list(self.selected_sensors_listbox.get(0, tk.END))
            
            for item in items:
                self.available_sensors_listbox.insert(tk.END, item)
            
            # Limpiar lista de seleccionados
            self.selected_sensors_listbox.delete(0, tk.END)
            
            self.update_selection_info()
            
        except Exception as e:
            print(f"Error deseleccionando todos los sensores: {e}")
    
    def update_selection_info(self):
        """Actualiza la información de sensores seleccionados"""
        selected_count = self.selected_sensors_listbox.size()
        available_count = self.available_sensors_listbox.size()
        total_count = selected_count + available_count
        
        info_text = f"{selected_count} de {total_count} sensores seleccionados"
        self.selection_info_label.config(text=info_text)
    
    def get_selected_sensors(self):
        """Retorna la lista de sensores seleccionados"""
        selected_sensors = []
        for i in range(self.selected_sensors_listbox.size()):
            sensor_text = self.selected_sensors_listbox.get(i)
            # Extraer ID del sensor del texto formato "SENSOR_ID (TYPE)"
            sensor_id = sensor_text.split(' (')[0] if ' (' in sensor_text else sensor_text
            selected_sensors.append(sensor_id)
        return selected_sensors
    
    
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
                                   command=print("Conectar/desconectar|"))
        connection_menu.add_command(label="Configurar Puerto", 
                                   command=print("configurar Puerto"))
    
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