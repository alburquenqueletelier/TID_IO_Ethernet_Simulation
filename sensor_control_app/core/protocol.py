"""
Protocol definitions for PET scan microcontroller communication.

This module defines the Layer 2 Ethernet protocol commands and their configurations
used to communicate with FPGAs (microcontrollers) in the PET scan system.
"""

# Comandos del protocolo (bytes hexadecimales)
COMMANDS = {
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

# Configuraciones de comandos con sus estados posibles
# Formato: {"nombre_visible": {"estado": "comando_real", ...}}
COMMAND_CONFIGS = {
    "X_02_TestTrigger": {
        "ON": "X_02_TestTrigger"
    },
    "X_03_RO_Single": {
        "ON": "X_03_RO_Single"
    },
    "X_04_RO_ON | X_05_RO_OFF": {
        "ON": "X_04_RO_ON",
        "OFF": "X_05_RO_OFF"
    },
    "X_08_DIAG_ | X_09_DIAG_DIS": {
        "ON": "X_08_DIAG_",
        "OFF": "X_09_DIAG_DIS"
    },
    "X_FB_TTrig_Auto_EN | X_FC_TTrig_Auto_DIS": {
        "ON": "X_FB_TTrig_Auto_EN",
        "OFF": "X_FC_TTrig_Auto_DIS",
    },
    "X_FF_Reset": {
        "ON": "X_FF_Reset"
    },
    "X_20_PwrDwnb_TOP_ON | X_21_PwrDwnb_TOP_OFF": {
        "ON": "X_20_PwrDwnb_TOP_ON",
        "OFF": "X_21_PwrDwnb_TOP_OFF"
    },
    "X_22_PwrDwnb_BOT_ON | X_23_PwrDwnb_BOT_OFF": {
        "ON": "X_22_PwrDwnb_BOT_ON",
        "OFF": "X_23_PwrDwnb_BOT_OFF",
    },
    "X_26_PwrEN_2V4D_ON | X_27_PwrEN_2V4D_OFF": {
        "ON": "X_26_PwrEN_2V4D_ON",
        "OFF": "X_27_PwrEN_2V4D_OFF"
    },
    "X_28_PwrEN_3V1_ON | X_29_PwrEN_3V1_OFF": {
        "ON": "X_28_PwrEN_3V1_ON",
        "OFF": "X_29_PwrEN_3V1_OFF"
    },
    "X_2A_PwrEN_1V8A_ON | X_2B_PwrEN_1V8A_OFF": {
        "ON": "X_2A_PwrEN_1V8A_ON",
        "OFF": "X_2B_PwrEN_1V8A_OFF"
    },
    "X_E1_FanSpeed0_High | X_E0_FanSpeed0_Low": {
        "HIGH": "X_E1_FanSpeed0_High",
        "LOW": "X_E0_FanSpeed0_Low"
    },
    "X_F9_TTrig_Global | X_FA_TTrig_Local": {
        "GLOBAL": "X_F9_TTrig_Global",
        "LOCAL": "X_FA_TTrig_Local"
    },
    "X_E3_FanSpeed1_High | X_E2_FanSpeed1_Low": {
        "HIGH": "X_E3_FanSpeed1_High",
        "LOW": "X_E2_FanSpeed1_Low"
    },
}


def get_command_byte(command_name: str) -> bytes:
    """
    Obtiene el byte correspondiente a un comando.

    Args:
        command_name: Nombre del comando (ej: "X_00_CPU")

    Returns:
        Byte del comando

    Raises:
        KeyError: Si el comando no existe
    """
    return COMMANDS[command_name]


def get_command_states(config_name: str) -> dict:
    """
    Obtiene los estados posibles de una configuración de comando.

    Args:
        config_name: Nombre de la configuración (ej: "X_04_RO_ON | X_05_RO_OFF")

    Returns:
        Diccionario con los estados posibles {"ON": "X_04_RO_ON", "OFF": "X_05_RO_OFF"}

    Raises:
        KeyError: Si la configuración no existe
    """
    return COMMAND_CONFIGS[config_name]


def is_valid_command(command_name: str) -> bool:
    """
    Verifica si un comando es válido.

    Args:
        command_name: Nombre del comando a verificar

    Returns:
        True si el comando existe, False en caso contrario
    """
    return command_name in COMMANDS


def is_valid_config(config_name: str) -> bool:
    """
    Verifica si una configuración de comando es válida.

    Args:
        config_name: Nombre de la configuración a verificar

    Returns:
        True si la configuración existe, False en caso contrario
    """
    return config_name in COMMAND_CONFIGS


def get_all_command_names() -> list:
    """
    Obtiene lista de todos los nombres de comandos disponibles.

    Returns:
        Lista de nombres de comandos
    """
    return list(COMMANDS.keys())


def get_all_config_names() -> list:
    """
    Obtiene lista de todos los nombres de configuraciones disponibles.

    Returns:
        Lista de nombres de configuraciones
    """
    return list(COMMAND_CONFIGS.keys())
