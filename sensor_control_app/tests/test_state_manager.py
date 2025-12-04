"""
Tests unitarios para el módulo state_manager.

Verifica que la gestión de estado funcione correctamente para
microcontroladores, asociaciones PET y macros.
"""

import unittest
import sys
import os

# Setup de path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from sensor_control_app.core.state_manager import StateManager
from sensor_control_app.core.models import MicroController, PETAssociation, Macro


class TestStateManagerInitialization(unittest.TestCase):
    """Tests para inicialización del StateManager"""

    def test_create_state_manager(self):
        """Verifica creación básica de StateManager"""
        sm = StateManager()

        self.assertIsNotNone(sm.mc_available)
        self.assertIsNotNone(sm.mc_registered)
        self.assertIsNotNone(sm.pet_associations)
        self.assertIsNotNone(sm.macros)

    def test_pet_associations_initialized(self):
        """Verifica que las asociaciones PET se inicialicen correctamente"""
        sm = StateManager()

        self.assertEqual(len(sm.pet_associations), 10)
        for i in range(1, 11):
            self.assertIn(i, sm.pet_associations)
            self.assertEqual(sm.pet_associations[i].pet_num, i)
            self.assertIsNone(sm.pet_associations[i].mc_mac)
            self.assertFalse(sm.pet_associations[i].enabled)


class TestStateManagerMicroControllers(unittest.TestCase):
    """Tests para gestión de microcontroladores"""

    def setUp(self):
        """Configuración antes de cada test"""
        self.sm = StateManager()

    def test_register_mc(self):
        """Verifica registro de microcontrolador"""
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC"
        )

        self.sm.register_mc(mc)

        self.assertIn("aa:bb:cc:dd:ee:ff", self.sm.mc_registered)
        self.assertEqual(self.sm.mc_registered["aa:bb:cc:dd:ee:ff"], mc)

    def test_unregister_mc(self):
        """Verifica eliminación de microcontrolador"""
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC"
        )

        self.sm.register_mc(mc)
        result = self.sm.unregister_mc("aa:bb:cc:dd:ee:ff")

        self.assertTrue(result)
        self.assertNotIn("aa:bb:cc:dd:ee:ff", self.sm.mc_registered)

    def test_unregister_nonexistent_mc(self):
        """Verifica eliminación de MC que no existe"""
        result = self.sm.unregister_mc("nonexistent:mac")

        self.assertFalse(result)

    def test_get_mc(self):
        """Verifica obtención de microcontrolador"""
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC"
        )

        self.sm.register_mc(mc)
        retrieved = self.sm.get_mc("aa:bb:cc:dd:ee:ff")

        self.assertEqual(retrieved, mc)

    def test_get_nonexistent_mc(self):
        """Verifica obtención de MC que no existe"""
        retrieved = self.sm.get_mc("nonexistent:mac")

        self.assertIsNone(retrieved)

    def test_get_mc_by_destiny(self):
        """Verifica obtención de MC por MAC de destino"""
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC"
        )

        self.sm.register_mc(mc)
        retrieved = self.sm.get_mc_by_destiny("ff:ee:dd:cc:bb:aa")

        self.assertEqual(retrieved, mc)

    def test_get_all_registered_mcs(self):
        """Verifica obtención de todos los MCs registrados"""
        mc1 = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="MC 1"
        )
        mc2 = MicroController(
            mac_source="11:22:33:44:55:66",
            mac_destiny="66:55:44:33:22:11",
            interface_destiny="eth1",
            label="MC 2"
        )

        self.sm.register_mc(mc1)
        self.sm.register_mc(mc2)

        all_mcs = self.sm.get_all_registered_mcs()

        self.assertEqual(len(all_mcs), 2)
        self.assertIn(mc1, all_mcs)
        self.assertIn(mc2, all_mcs)

    def test_update_mc_available(self):
        """Verifica actualización de MCs disponibles"""
        available = {
            "aa:bb:cc:dd:ee:ff": "eth0",
            "11:22:33:44:55:66": "eth1"
        }

        self.sm.update_mc_available(available)

        self.assertEqual(self.sm.mc_available, available)


class TestStateManagerPETAssociations(unittest.TestCase):
    """Tests para gestión de asociaciones PET"""

    def setUp(self):
        """Configuración antes de cada test"""
        self.sm = StateManager()

    def test_associate_pet(self):
        """Verifica asociación de PET con MC"""
        self.sm.associate_pet(1, "aa:bb:cc:dd:ee:ff", enabled=True)

        pet = self.sm.get_pet_association(1)
        self.assertEqual(pet.mc_mac, "aa:bb:cc:dd:ee:ff")
        self.assertTrue(pet.enabled)

    def test_associate_pet_invalid_number(self):
        """Verifica error al asociar PET con número inválido"""
        with self.assertRaises(ValueError):
            self.sm.associate_pet(11, "aa:bb:cc:dd:ee:ff")

        with self.assertRaises(ValueError):
            self.sm.associate_pet(0, "aa:bb:cc:dd:ee:ff")

    def test_get_pet_association(self):
        """Verifica obtención de asociación PET"""
        self.sm.associate_pet(5, "aa:bb:cc:dd:ee:ff", enabled=True)

        pet = self.sm.get_pet_association(5)

        self.assertIsNotNone(pet)
        self.assertEqual(pet.pet_num, 5)
        self.assertEqual(pet.mc_mac, "aa:bb:cc:dd:ee:ff")

    def test_get_enabled_pet_mcs(self):
        """Verifica obtención de MACs de PETs habilitados"""
        self.sm.associate_pet(1, "aa:bb:cc:dd:ee:ff", enabled=True)
        self.sm.associate_pet(2, "11:22:33:44:55:66", enabled=False)
        self.sm.associate_pet(3, "77:88:99:aa:bb:cc", enabled=True)

        enabled_macs = self.sm.get_enabled_pet_mcs()

        self.assertEqual(len(enabled_macs), 2)
        self.assertIn("aa:bb:cc:dd:ee:ff", enabled_macs)
        self.assertIn("77:88:99:aa:bb:cc", enabled_macs)
        self.assertNotIn("11:22:33:44:55:66", enabled_macs)

    def test_get_pets_by_mc(self):
        """Verifica obtención de PETs asociados a un MC"""
        self.sm.associate_pet(1, "aa:bb:cc:dd:ee:ff")
        self.sm.associate_pet(3, "aa:bb:cc:dd:ee:ff")
        self.sm.associate_pet(5, "11:22:33:44:55:66")

        pets = self.sm.get_pets_by_mc("aa:bb:cc:dd:ee:ff")

        self.assertEqual(len(pets), 2)
        self.assertIn(1, pets)
        self.assertIn(3, pets)
        self.assertNotIn(5, pets)


class TestStateManagerMacros(unittest.TestCase):
    """Tests para gestión de macros"""

    def setUp(self):
        """Configuración antes de cada test"""
        self.sm = StateManager()

    def test_save_universal_macro(self):
        """Verifica guardado de macro universal"""
        macro = Macro(
            name="TestMacro",
            command_configs={"cmd": {"ON": "X_00"}},
            last_state={"cmd": "ON"}
        )

        self.sm.save_macro(macro)

        self.assertIn("TestMacro", self.sm.macros)
        self.assertEqual(self.sm.macros["TestMacro"], macro)

    def test_save_mc_specific_macro(self):
        """Verifica guardado de macro específica de MC"""
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC"
        )
        self.sm.register_mc(mc)

        macro = Macro(
            name="MCMacro",
            command_configs={"cmd": {"ON": "X_00"}},
            last_state={"cmd": "ON"}
        )

        self.sm.save_macro(macro, mc_mac="aa:bb:cc:dd:ee:ff")

        retrieved_mc = self.sm.get_mc("aa:bb:cc:dd:ee:ff")
        self.assertIn("MCMacro", retrieved_mc.macros)

    def test_save_macro_nonexistent_mc(self):
        """Verifica error al guardar macro en MC inexistente"""
        macro = Macro(name="TestMacro")

        with self.assertRaises(ValueError):
            self.sm.save_macro(macro, mc_mac="nonexistent:mac")

    def test_load_universal_macro(self):
        """Verifica carga de macro universal"""
        macro = Macro(name="TestMacro")
        self.sm.save_macro(macro)

        loaded = self.sm.load_macro("TestMacro")

        self.assertEqual(loaded, macro)

    def test_load_mc_specific_macro(self):
        """Verifica carga de macro específica de MC"""
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC"
        )
        self.sm.register_mc(mc)

        macro = Macro(name="MCMacro")
        self.sm.save_macro(macro, mc_mac="aa:bb:cc:dd:ee:ff")

        loaded = self.sm.load_macro("MCMacro", mc_mac="aa:bb:cc:dd:ee:ff")

        self.assertEqual(loaded, macro)

    def test_load_nonexistent_macro(self):
        """Verifica carga de macro que no existe"""
        loaded = self.sm.load_macro("NonexistentMacro")

        self.assertIsNone(loaded)

    def test_delete_universal_macro(self):
        """Verifica eliminación de macro universal"""
        macro = Macro(name="TestMacro")
        self.sm.save_macro(macro)

        result = self.sm.delete_macro("TestMacro")

        self.assertTrue(result)
        self.assertNotIn("TestMacro", self.sm.macros)

    def test_delete_mc_specific_macro(self):
        """Verifica eliminación de macro específica de MC"""
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC"
        )
        self.sm.register_mc(mc)

        macro = Macro(name="MCMacro")
        self.sm.save_macro(macro, mc_mac="aa:bb:cc:dd:ee:ff")

        result = self.sm.delete_macro("MCMacro", mc_mac="aa:bb:cc:dd:ee:ff")

        self.assertTrue(result)
        retrieved_mc = self.sm.get_mc("aa:bb:cc:dd:ee:ff")
        self.assertNotIn("MCMacro", retrieved_mc.macros)

    def test_delete_nonexistent_macro(self):
        """Verifica eliminación de macro que no existe"""
        result = self.sm.delete_macro("NonexistentMacro")

        self.assertFalse(result)

    def test_list_universal_macros(self):
        """Verifica listado de macros universales"""
        self.sm.save_macro(Macro(name="Macro1"))
        self.sm.save_macro(Macro(name="Macro2"))

        macros = self.sm.list_macros()

        self.assertEqual(len(macros), 2)
        self.assertIn("Macro1", macros)
        self.assertIn("Macro2", macros)

    def test_list_mc_specific_macros(self):
        """Verifica listado de macros específicas de MC"""
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC"
        )
        self.sm.register_mc(mc)

        self.sm.save_macro(Macro(name="MCMacro1"), mc_mac="aa:bb:cc:dd:ee:ff")
        self.sm.save_macro(Macro(name="MCMacro2"), mc_mac="aa:bb:cc:dd:ee:ff")

        macros = self.sm.list_macros(mc_mac="aa:bb:cc:dd:ee:ff")

        self.assertEqual(len(macros), 2)
        self.assertIn("MCMacro1", macros)
        self.assertIn("MCMacro2", macros)


class TestStateManagerSerialization(unittest.TestCase):
    """Tests para serialización/deserialización de estado"""

    def setUp(self):
        """Configuración antes de cada test"""
        self.sm = StateManager()

    def test_to_dict(self):
        """Verifica conversión de estado a diccionario"""
        # Agregar datos de prueba
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC"
        )
        self.sm.register_mc(mc)
        self.sm.associate_pet(1, "ff:ee:dd:cc:bb:aa", enabled=True)
        self.sm.save_macro(Macro(name="TestMacro"))

        state_dict = self.sm.to_dict()

        self.assertIsInstance(state_dict, dict)
        self.assertIn("mc_available", state_dict)
        self.assertIn("mc_registered", state_dict)
        self.assertIn("pet_associations", state_dict)
        self.assertIn("macros", state_dict)


if __name__ == '__main__':
    unittest.main()
