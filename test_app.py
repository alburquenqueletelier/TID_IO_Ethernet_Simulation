import unittest
import tkinter as tk
from tkinter import ttk
import sys
import os

# Agregar el directorio actual al path para importar sensor_control_app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sensor_control_app import McControlApp


class TestScrollAndDragDrop(unittest.TestCase):
    """Tests para verificar funcionalidad de scroll y drag & drop"""

    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        cls.root = tk.Tk()
        cls.root.withdraw()  # Ocultar ventana durante tests

    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todos los tests"""
        cls.root.destroy()

    def setUp(self):
        """Configuración antes de cada test"""
        self.app = McControlApp(self.root)
        self.root.update_idletasks()

    def tearDown(self):
        """Limpieza después de cada test"""
        # Limpiar datos de prueba
        if hasattr(self.app, 'mc_registered'):
            self.app.mc_registered.clear()
        if hasattr(self.app, 'command_rows'):
            self.app.command_rows.clear()

    # ==================== TESTS DE SCROLL ====================

    def test_dashboard_scroll_exists(self):
        """Verifica que el canvas del dashboard tenga scroll configurado"""
        # Buscar el canvas en la pestaña dashboard
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
        
        # Verificar que el scrollbar está conectado al canvas
        # scrollbar.cget('command') devuelve un string como '139895404711040yview'
        # Verificamos que termine en 'yview' y que el canvas tenga yscrollcommand configurado
        command = scrollbar.cget('command')
        self.assertTrue(str(command).endswith('yview'), 
                    f"Scrollbar command no está configurado correctamente: {command}")
        
        # Verificar que el canvas tiene yscrollcommand configurado
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
        
        # Verificar bindings de scroll
        bindings = canvas.bind()
        
        # Verificar que existe al menos un binding de mousewheel
        has_mousewheel = any('<MouseWheel>' in str(b) or '<Button-4>' in str(b) or '<Button-5>' in str(b) 
                            for b in bindings)
        
        self.assertTrue(has_mousewheel, "No hay bindings de scroll en el canvas del dashboard")

    def test_commands_scroll_exists(self):
        """Verifica que el canvas de comandos tenga scroll configurado"""
        # Buscar el canvas en la pestaña de comandos
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
        
        # Verificar que el scrollbar está conectado al canvas
        command = scrollbar.cget('command')
        self.assertTrue(str(command).endswith('yview'), 
                    f"Scrollbar command no está configurado correctamente: {command}")
        
        # Verificar que el canvas tiene yscrollcommand configurado
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
        
        # Verificar bindings de scroll
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
        
        # Forzar actualización
        self.root.update_idletasks()
        
        # Verificar que scrollregion está configurado
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
        # Crear un MC de prueba y cargar comandos
        self.app.mc_registered["aa:bb:cc:dd:ee:ff"] = {
            "mac_destiny": "ff:ee:dd:cc:bb:aa",
            "interface_destiny": "eth0",
            "label": "Test MC",
            "command_configs": {
                "X_04_RO_ON | X_05_RO_OFF": {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"}
            },
            "last_state": {
                "X_04_RO_ON | X_05_RO_OFF": "ON"
            }
        }
        
        # Actualizar lista de MCs
        self.app.mc_combo['values'] = self.app.get_mc_display_list()
        self.app.mc_var.set(self.app.get_mc_display_list()[0])
        
        # Reconstruir tabla de comandos
        self.app.rebuild_command_table()
        self.root.update_idletasks()
        
        # Verificar que hay filas
        self.assertGreater(len(self.app.command_rows), 0, 
                          "No hay filas de comandos")
        
        # Verificar bindings en la primera fila
        if len(self.app.command_rows) > 0:
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
        # Crear MC de prueba con múltiples comandos
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
                "X_08_DIAG_ | X_09_DIAG_DIS": "OFF"
            }
        }
        
        # Actualizar y seleccionar MC
        self.app.mc_combo['values'] = self.app.get_mc_display_list()
        self.app.mc_var.set(self.app.get_mc_display_list()[0])
        self.app.rebuild_command_table()
        self.root.update_idletasks()
        
        # Obtener orden inicial
        initial_order = [row['cmd_name'] for row in self.app.command_rows]
        
        # Reordenar comandos (si hay al menos 2)
        if len(initial_order) >= 2:
            self.app.reorder_commands(initial_order[0], initial_order[1])
            self.root.update_idletasks()
            
            # Verificar que el orden cambió
            new_order = [row['cmd_name'] for row in self.app.command_rows]
            self.assertNotEqual(initial_order, new_order, 
                              "El orden no cambió después de reordenar")

    def test_drag_state_variables(self):
        """Verifica que las variables de estado de drag existan"""
        # Simular inicio de drag
        test_frame = tk.Frame(self.root)
        self.app.setup_drag_and_drop(test_frame, "TEST_CMD")
        
        # Estas variables se crean al iniciar drag
        self.assertTrue(hasattr(self.app, 'dragging'), 
                       "Variable dragging no existe")
        self.assertTrue(hasattr(self.app, 'drag_source'), 
                       "Variable drag_source no existe")

    # ==================== TESTS DE INTEGRACIÓN ====================

    def test_scroll_works_with_drag_drop(self):
        """Verifica que scroll y drag & drop coexistan sin conflictos"""
        # Crear MC con comandos
        self.app.mc_registered["aa:bb:cc:dd:ee:ff"] = {
            "mac_destiny": "ff:ee:dd:cc:bb:aa",
            "interface_destiny": "eth0",
            "label": "Test MC",
            "command_configs": {
                "X_04_RO_ON | X_05_RO_OFF": {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"}
            },
            "last_state": {
                "X_04_RO_ON | X_05_RO_OFF": "ON"
            }
        }
        
        # Cambiar a pestaña de comandos
        self.app.notebook.select(1)
        self.app.mc_combo['values'] = self.app.get_mc_display_list()
        self.app.mc_var.set(self.app.get_mc_display_list()[0])
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
        # Crear MC con comandos
        self.app.mc_registered["aa:bb:cc:dd:ee:ff"] = {
            "mac_destiny": "ff:ee:dd:cc:bb:aa",
            "interface_destiny": "eth0",
            "label": "Test MC",
            "command_configs": {
                "X_04_RO_ON | X_05_RO_OFF": {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"}
            },
            "last_state": {
                "X_04_RO_ON | X_05_RO_OFF": "ON"
            }
        }
        
        # Seleccionar MC y construir tabla
        self.app.mc_combo['values'] = self.app.get_mc_display_list()
        self.app.mc_var.set(self.app.get_mc_display_list()[0])
        self.app.rebuild_command_table()
        self.root.update_idletasks()
        
        # Obtener canvas
        commands_frame = self.app.notebook.nametowidget(self.app.notebook.tabs()[1])
        canvas = None
        for child in commands_frame.winfo_children():
            if isinstance(child, tk.Canvas):
                canvas = child
                break
        
        # Verificar scroll antes de rebuild
        bindings_before = canvas.bind()
        has_scroll_before = any('<MouseWheel>' in str(b) for b in bindings_before)
        self.assertTrue(has_scroll_before, "Scroll no funciona antes de rebuild")
        
        # Reconstruir tabla
        self.app.rebuild_command_table()
        self.root.update_idletasks()
        
        # Esperar a que bind_scroll_to_new_rows se ejecute
        self.root.after(200)
        self.root.update_idletasks()
        
        # Verificar scroll después de rebuild
        bindings_after = canvas.bind()
        has_scroll_after = any('<MouseWheel>' in str(b) for b in bindings_after)
        self.assertTrue(has_scroll_after, "Scroll no funciona después de rebuild")


def run_tests():
    """Ejecuta todos los tests y muestra resultados"""
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestScrollAndDragDrop)
    
    # Ejecutar tests con verbose output
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