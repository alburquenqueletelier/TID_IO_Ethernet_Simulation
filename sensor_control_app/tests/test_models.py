"""
Tests unitarios para el módulo models.

Verifica que los modelos de datos (dataclasses) funcionen correctamente
y que la serialización/deserialización sea correcta.
"""

import unittest
import sys
import os

# Setup de path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from sensor_control_app.core.models import (
    MicroController,
    PETAssociation,
    Macro,
    CommandInfo
)


class TestMicroController(unittest.TestCase):
    """Tests para el modelo MicroController"""

    def test_create_microcontroller(self):
        """Verifica creación básica de MicroController"""
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC"
        )

        self.assertEqual(mc.mac_source, "aa:bb:cc:dd:ee:ff")
        self.assertEqual(mc.mac_destiny, "ff:ee:dd:cc:bb:aa")
        self.assertEqual(mc.interface_destiny, "eth0")
        self.assertEqual(mc.label, "Test MC")
        self.assertEqual(mc.command_configs, {})
        self.assertEqual(mc.last_state, {})
        self.assertEqual(mc.macros, {})

    def test_microcontroller_with_configs(self):
        """Verifica MicroController con configuraciones"""
        configs = {
            "X_04_RO_ON | X_05_RO_OFF": {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"}
        }
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC",
            command_configs=configs
        )

        self.assertEqual(mc.command_configs, configs)

    def test_microcontroller_to_dict(self):
        """Verifica conversión de MicroController a diccionario"""
        mc = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC"
        )

        mc_dict = mc.to_dict()

        self.assertIsInstance(mc_dict, dict)
        self.assertEqual(mc_dict["mac_destiny"], "ff:ee:dd:cc:bb:aa")
        self.assertEqual(mc_dict["interface_destiny"], "eth0")
        self.assertEqual(mc_dict["label"], "Test MC")
        self.assertIn("command_configs", mc_dict)
        self.assertIn("last_state", mc_dict)
        self.assertIn("macros", mc_dict)

    def test_microcontroller_from_dict(self):
        """Verifica creación de MicroController desde diccionario"""
        data = {
            "mac_destiny": "ff:ee:dd:cc:bb:aa",
            "interface_destiny": "eth0",
            "label": "Test MC",
            "command_configs": {},
            "last_state": {},
            "macros": {}
        }

        mc = MicroController.from_dict("aa:bb:cc:dd:ee:ff", data)

        self.assertEqual(mc.mac_source, "aa:bb:cc:dd:ee:ff")
        self.assertEqual(mc.mac_destiny, "ff:ee:dd:cc:bb:aa")
        self.assertEqual(mc.interface_destiny, "eth0")
        self.assertEqual(mc.label, "Test MC")

    def test_microcontroller_roundtrip(self):
        """Verifica que to_dict -> from_dict preserve los datos"""
        original = MicroController(
            mac_source="aa:bb:cc:dd:ee:ff",
            mac_destiny="ff:ee:dd:cc:bb:aa",
            interface_destiny="eth0",
            label="Test MC",
            command_configs={"cmd": {"ON": "X_00"}},
            last_state={"cmd": "ON"}
        )

        # Convertir a dict y volver a crear
        mc_dict = original.to_dict()
        restored = MicroController.from_dict("aa:bb:cc:dd:ee:ff", mc_dict)

        self.assertEqual(restored.mac_source, original.mac_source)
        self.assertEqual(restored.mac_destiny, original.mac_destiny)
        self.assertEqual(restored.interface_destiny, original.interface_destiny)
        self.assertEqual(restored.label, original.label)
        self.assertEqual(restored.command_configs, original.command_configs)
        self.assertEqual(restored.last_state, original.last_state)


class TestPETAssociation(unittest.TestCase):
    """Tests para el modelo PETAssociation"""

    def test_create_pet_association(self):
        """Verifica creación básica de PETAssociation"""
        pet = PETAssociation(pet_num=1)

        self.assertEqual(pet.pet_num, 1)
        self.assertIsNone(pet.mc_mac)
        self.assertFalse(pet.enabled)

    def test_pet_association_with_mc(self):
        """Verifica PETAssociation con MC asociado"""
        pet = PETAssociation(
            pet_num=1,
            mc_mac="aa:bb:cc:dd:ee:ff",
            enabled=True
        )

        self.assertEqual(pet.pet_num, 1)
        self.assertEqual(pet.mc_mac, "aa:bb:cc:dd:ee:ff")
        self.assertTrue(pet.enabled)

    def test_pet_association_to_dict(self):
        """Verifica conversión de PETAssociation a diccionario"""
        pet = PETAssociation(
            pet_num=1,
            mc_mac="aa:bb:cc:dd:ee:ff",
            enabled=True
        )

        pet_dict = pet.to_dict()

        self.assertIsInstance(pet_dict, dict)
        self.assertEqual(pet_dict["mc"], "aa:bb:cc:dd:ee:ff")
        self.assertTrue(pet_dict["enabled"])

    def test_pet_association_from_dict(self):
        """Verifica creación de PETAssociation desde diccionario"""
        data = {
            "mc": "aa:bb:cc:dd:ee:ff",
            "enabled": True
        }

        pet = PETAssociation.from_dict(1, data)

        self.assertEqual(pet.pet_num, 1)
        self.assertEqual(pet.mc_mac, "aa:bb:cc:dd:ee:ff")
        self.assertTrue(pet.enabled)

    def test_pet_association_roundtrip(self):
        """Verifica que to_dict -> from_dict preserve los datos"""
        original = PETAssociation(
            pet_num=5,
            mc_mac="aa:bb:cc:dd:ee:ff",
            enabled=True
        )

        pet_dict = original.to_dict()
        restored = PETAssociation.from_dict(5, pet_dict)

        self.assertEqual(restored.pet_num, original.pet_num)
        self.assertEqual(restored.mc_mac, original.mc_mac)
        self.assertEqual(restored.enabled, original.enabled)


class TestMacro(unittest.TestCase):
    """Tests para el modelo Macro"""

    def test_create_macro(self):
        """Verifica creación básica de Macro"""
        macro = Macro(name="TestMacro")

        self.assertEqual(macro.name, "TestMacro")
        self.assertEqual(macro.command_configs, {})
        self.assertEqual(macro.last_state, {})

    def test_macro_with_configs(self):
        """Verifica Macro con configuraciones"""
        configs = {
            "X_04_RO_ON | X_05_RO_OFF": {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"}
        }
        state = {
            "X_04_RO_ON | X_05_RO_OFF": "ON"
        }

        macro = Macro(
            name="TestMacro",
            command_configs=configs,
            last_state=state
        )

        self.assertEqual(macro.name, "TestMacro")
        self.assertEqual(macro.command_configs, configs)
        self.assertEqual(macro.last_state, state)

    def test_macro_to_dict(self):
        """Verifica conversión de Macro a diccionario"""
        macro = Macro(
            name="TestMacro",
            command_configs={"cmd": {"ON": "X_00"}},
            last_state={"cmd": "ON"}
        )

        macro_dict = macro.to_dict()

        self.assertIsInstance(macro_dict, dict)
        self.assertIn("command_configs", macro_dict)
        self.assertIn("last_state", macro_dict)
        self.assertEqual(macro_dict["command_configs"], {"cmd": {"ON": "X_00"}})
        self.assertEqual(macro_dict["last_state"], {"cmd": "ON"})

    def test_macro_from_dict(self):
        """Verifica creación de Macro desde diccionario"""
        data = {
            "command_configs": {"cmd": {"ON": "X_00"}},
            "last_state": {"cmd": "ON"}
        }

        macro = Macro.from_dict("TestMacro", data)

        self.assertEqual(macro.name, "TestMacro")
        self.assertEqual(macro.command_configs, {"cmd": {"ON": "X_00"}})
        self.assertEqual(macro.last_state, {"cmd": "ON"})

    def test_macro_roundtrip(self):
        """Verifica que to_dict -> from_dict preserve los datos"""
        original = Macro(
            name="TestMacro",
            command_configs={"cmd": {"ON": "X_00", "OFF": "X_01"}},
            last_state={"cmd": "OFF"}
        )

        macro_dict = original.to_dict()
        restored = Macro.from_dict("TestMacro", macro_dict)

        self.assertEqual(restored.name, original.name)
        self.assertEqual(restored.command_configs, original.command_configs)
        self.assertEqual(restored.last_state, original.last_state)


class TestCommandInfo(unittest.TestCase):
    """Tests para el modelo CommandInfo"""

    def test_create_command_info(self):
        """Verifica creación básica de CommandInfo"""
        cmd = CommandInfo(
            config_name="X_FF_Reset",
            command_name="X_FF_Reset",
            command_byte=b"\xff"
        )

        self.assertEqual(cmd.config_name, "X_FF_Reset")
        self.assertEqual(cmd.command_name, "X_FF_Reset")
        self.assertEqual(cmd.command_byte, b"\xff")
        self.assertEqual(cmd.repetitions, 1)
        self.assertEqual(cmd.delay_ms, 0)

    def test_command_info_with_repetitions(self):
        """Verifica CommandInfo con repeticiones"""
        cmd = CommandInfo(
            config_name="X_02_TestTrigger",
            command_name="X_02_TestTrigger",
            command_byte=b"\x02",
            repetitions=10,
            delay_ms=100
        )

        self.assertEqual(cmd.repetitions, 10)
        self.assertEqual(cmd.delay_ms, 100)

    def test_command_info_repr(self):
        """Verifica representación de CommandInfo"""
        cmd = CommandInfo(
            config_name="X_02_TestTrigger",
            command_name="X_02_TestTrigger",
            command_byte=b"\x02",
            repetitions=5,
            delay_ms=50
        )

        repr_str = repr(cmd)
        self.assertIn("X_02_TestTrigger", repr_str)
        self.assertIn("5", repr_str)
        self.assertIn("50", repr_str)


if __name__ == '__main__':
    unittest.main()
