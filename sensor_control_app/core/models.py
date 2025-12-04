"""
Data models for the PET scan control application.

This module defines the core data structures using dataclasses for type safety
and better code organization.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class MicroController:
    """
    Representa un microcontrolador (FPGA) registrado en el sistema.

    Attributes:
        mac_source: Dirección MAC de origen (interfaz local)
        mac_destiny: Dirección MAC de destino (microcontrolador)
        interface_destiny: Nombre de la interfaz de red (ej: "eth0")
        label: Etiqueta descriptiva del microcontrolador
        command_configs: Configuración de comandos {config_name: {state: command}}
        last_state: Último estado conocido de comandos {config_name: state, config_name_delta: float}
        macros: Macros específicas de este MC {macro_name: Macro}
    """
    mac_source: str
    mac_destiny: str
    interface_destiny: str
    label: str
    command_configs: Dict[str, Dict[str, str]] = field(default_factory=dict)
    last_state: Dict[str, Any] = field(default_factory=dict)
    macros: Dict[str, 'Macro'] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Convierte el MicroController a diccionario para serialización.

        Returns:
            Diccionario con los datos del microcontrolador
        """
        return {
            "mac_destiny": self.mac_destiny,
            "interface_destiny": self.interface_destiny,
            "label": self.label,
            "command_configs": self.command_configs,
            "last_state": self.last_state,
            "macros": {name: macro.to_dict() for name, macro in self.macros.items()}
        }

    @staticmethod
    def from_dict(mac_source: str, data: dict) -> 'MicroController':
        """
        Crea un MicroController desde un diccionario.

        Args:
            mac_source: Dirección MAC de origen
            data: Diccionario con los datos del microcontrolador

        Returns:
            Instancia de MicroController
        """
        # Convertir macros de dict a objetos Macro
        macros_dict = {}
        if "macros" in data:
            for macro_name, macro_data in data["macros"].items():
                macros_dict[macro_name] = Macro.from_dict(macro_name, macro_data)

        return MicroController(
            mac_source=mac_source,
            mac_destiny=data.get("mac_destiny", ""),
            interface_destiny=data.get("interface_destiny", ""),
            label=data.get("label", ""),
            command_configs=data.get("command_configs", {}),
            last_state=data.get("last_state", {}),
            macros=macros_dict
        )


@dataclass
class PETAssociation:
    """
    Representa la asociación entre un PET scanner y un microcontrolador.

    Attributes:
        pet_num: Número del PET scanner (1-10)
        mc_mac: Dirección MAC del microcontrolador asociado (None si no hay asociación)
        enabled: Si el PET scanner está habilitado para recibir comandos
    """
    pet_num: int
    mc_mac: Optional[str] = None
    enabled: bool = False

    def to_dict(self) -> dict:
        """
        Convierte la asociación PET a diccionario para serialización.

        Returns:
            Diccionario con los datos de la asociación
        """
        return {
            "mc": self.mc_mac,
            "enabled": self.enabled
        }

    @staticmethod
    def from_dict(pet_num: int, data: dict) -> 'PETAssociation':
        """
        Crea una PETAssociation desde un diccionario.

        Args:
            pet_num: Número del PET scanner
            data: Diccionario con los datos de la asociación

        Returns:
            Instancia de PETAssociation
        """
        return PETAssociation(
            pet_num=pet_num,
            mc_mac=data.get("mc"),
            enabled=data.get("enabled", False)
        )


@dataclass
class Macro:
    """
    Representa una macro de comandos reutilizable.

    Las macros pueden ser universales (compartidas entre todos los MCs) o
    específicas de un microcontrolador.

    Attributes:
        name: Nombre de la macro
        command_configs: Configuración de comandos de la macro
        last_state: Estado guardado de los comandos
    """
    name: str
    command_configs: Dict[str, Dict[str, str]] = field(default_factory=dict)
    last_state: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """
        Convierte la Macro a diccionario para serialización.

        Returns:
            Diccionario con los datos de la macro
        """
        return {
            "command_configs": self.command_configs,
            "last_state": self.last_state
        }

    @staticmethod
    def from_dict(name: str, data: dict) -> 'Macro':
        """
        Crea una Macro desde un diccionario.

        Args:
            name: Nombre de la macro
            data: Diccionario con los datos de la macro

        Returns:
            Instancia de Macro
        """
        return Macro(
            name=name,
            command_configs=data.get("command_configs", {}),
            last_state=data.get("last_state", {})
        )


@dataclass
class CommandInfo:
    """
    Información sobre un comando a enviar.

    Attributes:
        config_name: Nombre de la configuración del comando
        command_name: Nombre específico del comando a enviar
        command_byte: Byte del comando
        repetitions: Número de repeticiones
        delay_ms: Delay entre repeticiones en milisegundos
    """
    config_name: str
    command_name: str
    command_byte: bytes
    repetitions: int = 1
    delay_ms: int = 0

    def __repr__(self) -> str:
        """Representación legible del comando"""
        return f"CommandInfo({self.command_name}, reps={self.repetitions}, delay={self.delay_ms}ms)"
