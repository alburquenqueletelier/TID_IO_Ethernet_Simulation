"""
Tests unitarios para el módulo protocol.

Verifica que el protocolo de comunicación esté correctamente definido
y que las funciones de acceso funcionen como esperado.
"""

import unittest
import sys
import os

# Setup de path
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, root_dir)

from sensor_control_app.core import protocol


class TestProtocolCommands(unittest.TestCase):
    """Tests para comandos del protocolo"""

    def test_commands_dict_exists(self):
        """Verifica que el diccionario COMMANDS exista"""
        self.assertIsNotNone(protocol.COMMANDS)
        self.assertIsInstance(protocol.COMMANDS, dict)

    def test_commands_not_empty(self):
        """Verifica que haya comandos definidos"""
        self.assertGreater(len(protocol.COMMANDS), 0)

    def test_command_bytes_are_bytes(self):
        """Verifica que todos los valores sean bytes"""
        for cmd_name, cmd_byte in protocol.COMMANDS.items():
            self.assertIsInstance(cmd_byte, bytes, f"{cmd_name} no es bytes")
            self.assertEqual(len(cmd_byte), 1, f"{cmd_name} no tiene exactamente 1 byte")

    def test_specific_commands_exist(self):
        """Verifica que comandos específicos existan"""
        required_commands = [
            "X_00_CPU",
            "X_02_TestTrigger",
            "X_FF_Reset",
            "X_04_RO_ON",
            "X_05_RO_OFF",
        ]
        for cmd in required_commands:
            self.assertIn(cmd, protocol.COMMANDS, f"Comando {cmd} no encontrado")

    def test_command_byte_values(self):
        """Verifica valores específicos de comandos"""
        self.assertEqual(protocol.COMMANDS["X_00_CPU"], b"\x00")
        self.assertEqual(protocol.COMMANDS["X_02_TestTrigger"], b"\x02")
        self.assertEqual(protocol.COMMANDS["X_FF_Reset"], b"\xff")
        self.assertEqual(protocol.COMMANDS["X_E0_FanSpeed0_Low"], b"\xe0")


class TestProtocolCommandConfigs(unittest.TestCase):
    """Tests para configuraciones de comandos"""

    def test_command_configs_exists(self):
        """Verifica que COMMAND_CONFIGS exista"""
        self.assertIsNotNone(protocol.COMMAND_CONFIGS)
        self.assertIsInstance(protocol.COMMAND_CONFIGS, dict)

    def test_command_configs_not_empty(self):
        """Verifica que haya configuraciones definidas"""
        self.assertGreater(len(protocol.COMMAND_CONFIGS), 0)

    def test_command_configs_structure(self):
        """Verifica la estructura de las configuraciones"""
        for config_name, states in protocol.COMMAND_CONFIGS.items():
            self.assertIsInstance(states, dict, f"{config_name} no es dict")
            self.assertGreater(len(states), 0, f"{config_name} no tiene estados")

            # Verificar que los estados apunten a comandos válidos
            for state, cmd_name in states.items():
                self.assertIsInstance(state, str, f"Estado en {config_name} no es string")
                self.assertIsInstance(cmd_name, str, f"Comando en {config_name} no es string")

    def test_specific_configs_exist(self):
        """Verifica que configuraciones específicas existan"""
        required_configs = [
            "X_04_RO_ON | X_05_RO_OFF",
            "X_FF_Reset",
            "X_E1_FanSpeed0_High | X_E0_FanSpeed0_Low",
        ]
        for config in required_configs:
            self.assertIn(config, protocol.COMMAND_CONFIGS, f"Config {config} no encontrada")

    def test_on_off_config(self):
        """Verifica una configuración ON/OFF típica"""
        config = protocol.COMMAND_CONFIGS["X_04_RO_ON | X_05_RO_OFF"]
        self.assertIn("ON", config)
        self.assertIn("OFF", config)
        self.assertEqual(config["ON"], "X_04_RO_ON")
        self.assertEqual(config["OFF"], "X_05_RO_OFF")

    def test_single_state_config(self):
        """Verifica una configuración de un solo estado"""
        config = protocol.COMMAND_CONFIGS["X_FF_Reset"]
        self.assertIn("ON", config)
        self.assertEqual(len(config), 1)


class TestProtocolFunctions(unittest.TestCase):
    """Tests para funciones del protocolo"""

    def test_get_command_byte_valid(self):
        """Verifica get_command_byte con comando válido"""
        cmd_byte = protocol.get_command_byte("X_00_CPU")
        self.assertEqual(cmd_byte, b"\x00")

    def test_get_command_byte_invalid(self):
        """Verifica get_command_byte con comando inválido"""
        with self.assertRaises(KeyError):
            protocol.get_command_byte("X_INVALID_CMD")

    def test_get_command_states_valid(self):
        """Verifica get_command_states con config válida"""
        states = protocol.get_command_states("X_04_RO_ON | X_05_RO_OFF")
        self.assertIn("ON", states)
        self.assertIn("OFF", states)

    def test_get_command_states_invalid(self):
        """Verifica get_command_states con config inválida"""
        with self.assertRaises(KeyError):
            protocol.get_command_states("INVALID_CONFIG")

    def test_is_valid_command_true(self):
        """Verifica is_valid_command con comando válido"""
        self.assertTrue(protocol.is_valid_command("X_00_CPU"))
        self.assertTrue(protocol.is_valid_command("X_FF_Reset"))

    def test_is_valid_command_false(self):
        """Verifica is_valid_command con comando inválido"""
        self.assertFalse(protocol.is_valid_command("X_INVALID"))
        self.assertFalse(protocol.is_valid_command(""))

    def test_is_valid_config_true(self):
        """Verifica is_valid_config con config válida"""
        self.assertTrue(protocol.is_valid_config("X_FF_Reset"))
        self.assertTrue(protocol.is_valid_config("X_04_RO_ON | X_05_RO_OFF"))

    def test_is_valid_config_false(self):
        """Verifica is_valid_config con config inválida"""
        self.assertFalse(protocol.is_valid_config("INVALID_CONFIG"))
        self.assertFalse(protocol.is_valid_config(""))

    def test_get_all_command_names(self):
        """Verifica get_all_command_names"""
        names = protocol.get_all_command_names()
        self.assertIsInstance(names, list)
        self.assertGreater(len(names), 0)
        self.assertIn("X_00_CPU", names)
        self.assertIn("X_FF_Reset", names)

    def test_get_all_config_names(self):
        """Verifica get_all_config_names"""
        names = protocol.get_all_config_names()
        self.assertIsInstance(names, list)
        self.assertGreater(len(names), 0)
        self.assertIn("X_FF_Reset", names)
        self.assertIn("X_04_RO_ON | X_05_RO_OFF", names)


class TestProtocolIntegrity(unittest.TestCase):
    """Tests de integridad del protocolo"""

    def test_all_config_commands_exist(self):
        """Verifica que todos los comandos referenciados en configs existan"""
        for config_name, states in protocol.COMMAND_CONFIGS.items():
            for state, cmd_name in states.items():
                self.assertIn(
                    cmd_name,
                    protocol.COMMANDS,
                    f"Comando '{cmd_name}' en config '{config_name}' no existe en COMMANDS"
                )

    def test_no_duplicate_command_bytes(self):
        """Verifica que no haya bytes duplicados (cada comando debe ser único)"""
        seen_bytes = set()
        duplicates = []

        for cmd_name, cmd_byte in protocol.COMMANDS.items():
            if cmd_byte in seen_bytes:
                duplicates.append(f"{cmd_name}: {cmd_byte.hex()}")
            seen_bytes.add(cmd_byte)

        self.assertEqual(
            len(duplicates),
            0,
            f"Se encontraron comandos con bytes duplicados: {duplicates}"
        )

    def test_config_names_match_pattern(self):
        """Verifica que los nombres de configs sigan el patrón esperado"""
        for config_name in protocol.COMMAND_CONFIGS.keys():
            # Debe ser un comando simple o comandos separados por " | "
            self.assertTrue(
                config_name.startswith("X_"),
                f"Config '{config_name}' no comienza con X_"
            )


if __name__ == '__main__':
    unittest.main()
