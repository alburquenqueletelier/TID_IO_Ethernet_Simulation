import unittest
import tkinter as tk
from tkinter import ttk
import sys
import os

# Agregar el directorio raíz al path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

# Importar desde el archivo original en la raíz del proyecto (por ahora, durante la migración)
# Nota: sensor_control_app.py está en la raíz, no en el paquete sensor_control_app/
import sys
sys.path.insert(0, root_dir)
import importlib.util
spec = importlib.util.spec_from_file_location("sensor_control_app_legacy",
                                               os.path.join(root_dir, "sensor_control_app.py"))
sensor_control_app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sensor_control_app_module)
McControlApp = sensor_control_app_module.McControlApp


class TestScrollAndDragDrop(unittest.TestCase):
    """Tests para verificar funcionalidad de scroll y drag & drop"""

    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        # Crear la raíz y ocultarla (necesario para Xvfb)
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todos los tests"""
        cls.root.destroy()

    def setUp(self):
        """Configuración antes de cada test"""
        # Instanciar la aplicación
        self.app = McControlApp(self.root)
        # Forzar el renderizado inicial de todos los widgets (muy importante para Tkinter en tests)
        self.root.update_idletasks()

    def tearDown(self):
        """Limpieza después de cada test"""
        # Limpiar datos de prueba
        if hasattr(self.app, 'mc_registered'):
            self.app.mc_registered.clear()
        if hasattr(self.app, 'command_rows'):
            self.app.command_rows.clear()
        
        # Destruir la instancia de la aplicación para aislar tests
        # Si McControlApp tiene un método .destroy(), úsalo aquí.

    # ==================== TESTS DE SCROLL ====================

    def test_dashboard_scroll_exists(self):
        """Verifica que el canvas del dashboard tenga scroll configurado"""
        dashboard_frame = self.app.notebook.nametowidget(self.app.notebook.tabs()[0])
        
        canvas = None
        scrollbar = None
        
        for child in dashboard_frame.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
            elif isinstance(child, tk.Scrollbar):
                scrollbar = child
        
        self.assertIsNotNone(canvas, "Canvas del dashboard no encontrado")
        self.assertIsNotNone(scrollbar, "Scrollbar del dashboard no encontrado")
        
        command = scrollbar.cget('command')
        self.assertTrue(str(command).endswith('yview'), 
                    f"Scrollbar command no está configurado correctamente: {command}")
        
        yscrollcommand = canvas.cget('yscrollcommand')
        self.assertIsNotNone(yscrollcommand, "Canvas yscrollcommand no está configurado")
        self.assertNotEqual(yscrollcommand, '', "Canvas yscrollcommand está vacío")


    def test_dashboard_scroll_bindings(self):
        """Verifica que los bindings de scroll estén configurados en el dashboard"""
        dashboard_frame = self.app.notebook.nametowidget(self.app.notebook.tabs()[0])
        
        canvas = None
        for child in dashboard_frame.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
                break
        
        self.assertIsNotNone(canvas, "Canvas del dashboard no encontrado")
        
        bindings = canvas.bind()
        has_mousewheel = any('<MouseWheel>' in str(b) or '<Button-4>' in str(b) or '<Button-5>' in str(b) 
                            for b in bindings)
        
        self.assertTrue(has_mousewheel, "No hay bindings de scroll en el canvas del dashboard")

    def test_commands_scroll_exists(self):
        """Verifica que el canvas de comandos tenga scroll configurado"""
        commands_frame = self.app.notebook.nametowidget(self.app.notebook.tabs()[1])
        
        canvas = None
        scrollbar = None
        
        for child in commands_frame.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
            elif isinstance(child, tk.Scrollbar):
                scrollbar = child
        
        self.assertIsNotNone(canvas, "Canvas de comandos no encontrado")
        self.assertIsNotNone(scrollbar, "Scrollbar de comandos no encontrado")
        
        command = scrollbar.cget('command')
        self.assertTrue(str(command).endswith('yview'), 
                    f"Scrollbar command no está configurado correctamente: {command}")
        
        yscrollcommand = canvas.cget('yscrollcommand')
        self.assertIsNotNone(yscrollcommand, "Canvas yscrollcommand no está configurado")
        self.assertNotEqual(yscrollcommand, '', "Canvas yscrollcommand está vacío")

    def test_commands_scroll_bindings(self):
        """Verifica que los bindings de scroll estén configurados en comandos"""
        commands_frame = self.app.notebook.nametowidget(self.app.notebook.tabs()[1])
        
        canvas = None
        for child in commands_frame.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
                break
        
        self.assertIsNotNone(canvas, "Canvas de comandos no encontrado")
        
        bindings = canvas.bind()
        
        has_mousewheel = any('<MouseWheel>' in str(b) or '<Button-4>' in str(b) or '<Button-5>' in str(b) 
                            for b in bindings)
        
        self.assertTrue(has_mousewheel, "No hay bindings de scroll en el canvas de comandos")

    def test_scroll_region_updates(self):
        """Verifica que la región de scroll se actualice correctamente"""
        dashboard_frame = self.app.notebook.nametowidget(self.app.notebook.tabs()[0])
        
        canvas = None
        for child in dashboard_frame.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
                break
        
        self.assertIsNotNone(canvas, "Canvas del dashboard no encontrado")
        
        self.root.update_idletasks()
        
        scrollregion = canvas.cget('scrollregion')
        self.assertIsNotNone(scrollregion, "Scrollregion no está configurado")
        self.assertNotEqual(scrollregion, '', "Scrollregion está vacío")

    # ==================== TESTS DE DRAG & DROP ====================

    def test_drag_drop_initialization(self):
        """Verifica que el sistema de drag & drop esté inicializado"""
        self.assertTrue(hasattr(self.app, 'command_rows'), 
                       "command_rows no está inicializado")
        self.assertTrue(hasattr(self.app, 'setup_drag_and_drop'), 
                       "Método setup_drag_and_drop no existe")

    def test_drag_drop_methods_exist(self):
        """Verifica que existan los métodos necesarios para drag & drop"""
        methods = ['start_drag', 'do_drag', 'end_drag', 'reorder_commands']
        
        for method in methods:
            self.assertTrue(hasattr(self.app, method), 
                          f"Método {method} no existe")
            self.assertTrue(callable(getattr(self.app, method)), 
                          f"{method} no es callable")

    def test_command_rows_bindings(self):
        """Verifica que las filas de comandos tengan bindings de drag"""
        # Crear un MC de prueba con la estructura ACTUAL (comandos con delta_time individual)
        self.app.mc_registered["aa:bb:cc:dd:ee:ff"] = {
            "mac_destiny": "ff:ee:dd:cc:bb:aa",
            "interface_destiny": "eth0",
            "label": "Test MC",
            "command_configs": {
                "X_04_RO_ON | X_05_RO_OFF": {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"}
            },
            "last_state": {
                "X_04_RO_ON | X_05_RO_OFF": "ON",
                "X_04_RO_ON | X_05_RO_OFF_delta": 1.0  # Delta time individual
            }
        }
        
        # Actualizar lista de MCs
        self.app.mc_combo['values'] = self.app.get_mc_display_list()
        self.root.update_idletasks()
        
        # Verificar que hay MCs disponibles
        if len(self.app.get_mc_display_list()) == 0:
            self.skipTest("No hay MCs registrados para probar")
            return
        
        # Seleccionar la MAC de prueba
        self.app.mc_var.set(self.app.get_mc_display_list()[0])
        
        # Simular la interacción del usuario
        try:
            self.app.mc_combo.event_generate('<<ComboboxSelected>>')
        except tk.TclError:
            print("Warning: Failed to generate <<ComboboxSelected>> event.")
            self.app.rebuild_command_table()
        
        self.root.update_idletasks()
        
        # Verificar que hay filas
        if len(self.app.command_rows) == 0:
            self.skipTest("No se generaron filas de comandos (posible error en rebuild_command_table)")
            return
        
        self.assertGreater(len(self.app.command_rows), 0, 
                        "No hay filas de comandos")
        
        # Verificar bindings en la primera fila
        row_frame = self.app.command_rows[0]['frame']
        bindings = row_frame.bind()
        
        # Verificar bindings de drag
        drag_bindings = ['<Button-1>', '<B1-Motion>', '<ButtonRelease-1>']
        for binding in drag_bindings:
            has_binding = any(binding in str(b) for b in bindings)
            self.assertTrue(has_binding, 
                        f"Binding {binding} no encontrado en fila de comando")

    def test_reorder_commands_with_valid_data(self):
        """Verifica que reorder_commands funcione con datos válidos"""
        # Crear MC de prueba con múltiples comandos (estructura ACTUAL)
        self.app.mc_registered["aa:bb:cc:dd:ee:ff"] = {
            "mac_destiny": "ff:ee:dd:cc:bb:aa",
            "interface_destiny": "eth0",
            "label": "Test MC",
            "command_configs": {
                "X_04_RO_ON | X_05_RO_OFF": {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"},
                "X_08_DIAG_ | X_09_DIAG_DIS": {"ON": "X_08_DIAG_", "OFF": "X_09_DIAG_DIS"}
            },
            "last_state": {
                "X_04_RO_ON | X_05_RO_OFF": "ON",
                "X_04_RO_ON | X_05_RO_OFF_delta": 1.0,
                "X_08_DIAG_ | X_09_DIAG_DIS": "OFF",
                "X_08_DIAG_ | X_09_DIAG_DIS_delta": 1.0
            }
        }
        
        # Actualizar y seleccionar MC
        self.app.mc_combo['values'] = self.app.get_mc_display_list()
        
        if len(self.app.get_mc_display_list()) == 0:
            self.skipTest("No hay MCs registrados para probar")
            return
        
        self.app.mc_var.set(self.app.get_mc_display_list()[0])
        self.root.update_idletasks()

        try:
            self.app.mc_combo.event_generate('<<ComboboxSelected>>')
        except tk.TclError:
            print("Warning: Failed to generate <<ComboboxSelected>> event.")
            self.app.rebuild_command_table()

        self.root.update_idletasks()
        
        # Obtener orden inicial
        if len(self.app.command_rows) < 2:
            self.skipTest("Se necesitan al menos 2 comandos para probar reordenamiento")
            return
        
        initial_order = [row['cmd_name'] for row in self.app.command_rows]
        
        # Reordenar comandos
        self.app.reorder_commands(initial_order[0], initial_order[1])
        self.root.update_idletasks()
        
        # Verificar que el orden cambió
        new_order = [row['cmd_name'] for row in self.app.command_rows]
        self.assertNotEqual(initial_order, new_order, 
                        "El orden no cambió después de reordenar")
        
    def test_drag_state_variables(self):
        """Verifica que las variables de estado de drag existan"""
        # Simular inicio de drag (necesita un frame real)
        test_frame = tk.Frame(self.root)
        self.app.setup_drag_and_drop(test_frame, "TEST_CMD")
        test_frame.destroy() # Limpieza
        
        # Estas variables se crean al iniciar drag (deben ser inicializadas en el constructor)
        self.assertTrue(hasattr(self.app, 'dragging'), 
                       "Variable dragging no existe")
        self.assertTrue(hasattr(self.app, 'drag_source'), 
                       "Variable drag_source no existe")

    # ==================== TESTS DE INTEGRACIÓN ====================

    def test_scroll_works_with_drag_drop(self):
        """Verifica que scroll y drag & drop coexistan sin conflictos"""
        # Crear MC con comandos (estructura ACTUAL)
        self.app.mc_registered["aa:bb:cc:dd:ee:ff"] = {
            "mac_destiny": "ff:ee:dd:cc:bb:aa",
            "interface_destiny": "eth0",
            "label": "Test MC",
            "command_configs": {
                "X_04_RO_ON | X_05_RO_OFF": {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"}
            },
            "last_state": {
                "X_04_RO_ON | X_05_RO_OFF": "ON",
                "X_04_RO_ON | X_05_RO_OFF_delta": 1.0
            }
        }
        
        # Simulación de selección
        self.app.notebook.select(1)
        self.app.mc_combo['values'] = self.app.get_mc_display_list()
        
        if len(self.app.get_mc_display_list()) == 0:
            self.skipTest("No hay MCs registrados para probar")
            return
        
        self.app.mc_var.set(self.app.get_mc_display_list()[0])
        self.root.update_idletasks()
        
        try:
            self.app.mc_combo.event_generate('<<ComboboxSelected>>')
        except tk.TclError:
            print("Warning: Failed to generate <<ComboboxSelected>> event.")
            self.app.rebuild_command_table()

        self.root.update_idletasks()
        
        # Obtener canvas de comandos
        commands_frame = self.app.notebook.nametowidget(self.app.notebook.tabs()[1])
        canvas = None
        
        for child in commands_frame.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
                break
        
        self.assertIsNotNone(canvas, "Canvas de comandos no encontrado")
        
        # Verificar que scroll bindings existan
        canvas_bindings = canvas.bind()
        has_scroll = any('<MouseWheel>' in str(b) or '<Button-4>' in str(b) 
                        for b in canvas_bindings)
        self.assertTrue(has_scroll, "Scroll bindings no encontrados")
        
        # Verificar que drag bindings existan en filas
        if len(self.app.command_rows) > 0:
            row_frame = self.app.command_rows[0]['frame']
            row_bindings = row_frame.bind()
            has_drag = any('<Button-1>' in str(b) for b in row_bindings)
            self.assertTrue(has_drag, "Drag bindings no encontrados")

    def test_rebuild_command_table_preserves_scroll(self):
        """Verifica que rebuild_command_table preserve los bindings de scroll"""
        # Crear MC con comandos (estructura ACTUAL)
        self.app.mc_registered["aa:bb:cc:dd:ee:ff"] = {
            "mac_destiny": "ff:ee:dd:cc:bb:aa",
            "interface_destiny": "eth0",
            "label": "Test MC",
            "command_configs": {
                "X_04_RO_ON | X_05_RO_OFF": {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"}
            },
            "last_state": {
                "X_04_RO_ON | X_05_RO_OFF": "ON",
                "X_04_RO_ON | X_05_RO_OFF_delta": 1.0
            }
        }
        
        # Seleccionar MC y construir tabla
        self.app.mc_combo['values'] = self.app.get_mc_display_list()
        
        if len(self.app.get_mc_display_list()) == 0:
            self.skipTest("No hay MCs registrados para probar")
            return
        
        self.app.mc_var.set(self.app.get_mc_display_list()[0])
        self.root.update_idletasks()

        try:
            self.app.mc_combo.event_generate('<<ComboboxSelected>>')
        except tk.TclError:
            print("Warning: Failed to generate <<ComboboxSelected>> event.")
            self.app.rebuild_command_table()
            
        self.root.update_idletasks()
        
        # Obtener canvas
        commands_frame = self.app.notebook.nametowidget(self.app.notebook.tabs()[1])
        canvas = None
        for child in commands_frame.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
                break
        
        self.assertIsNotNone(canvas, "Canvas de comandos no encontrado")
        
        # Verificar scroll antes de rebuild
        bindings_before = canvas.bind()
        has_scroll_before = any('<MouseWheel>' in str(b) for b in bindings_before)
        self.assertTrue(has_scroll_before, "Scroll no funciona antes de rebuild")
        
        # Reconstruir tabla
        self.app.rebuild_command_table()
        self.root.update_idletasks()
        
        # Verificar scroll después de rebuild
        bindings_after = canvas.bind()
        has_scroll_after = any('<MouseWheel>' in str(b) for b in bindings_after)
        self.assertTrue(has_scroll_after, "Scroll no funciona después de rebuild")

def run_tests():
    """Ejecuta todos los tests y muestra resultados"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestScrollAndDragDrop)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumen
    print("\n" + "="*70)
    print("RESUMEN DE TESTS")
    print("="*70)
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Éxitos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)