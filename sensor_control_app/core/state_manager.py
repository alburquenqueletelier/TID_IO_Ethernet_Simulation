"""
State management for the PET scan control application.

This module provides centralized state management for microcontrollers,
PET scanner associations, and macros.
"""

from typing import Dict, List, Optional
from .models import MicroController, PETAssociation, Macro


class StateManager:
    """
    Gestiona el estado de la aplicación.

    Mantiene el registro de microcontroladores disponibles y registrados,
    asociaciones de PET scanners, y macros universales.
    """

    def __init__(self, database=None):
        """
        Inicializa el StateManager.

        Args:
            database: Instancia de Database para persistencia (opcional)
        """
        self.database = database

        # Microcontroladores disponibles {mac_source: interface_name}
        self.mc_available: Dict[str, str] = {}

        # Microcontroladores registrados {mac_source: MicroController}
        self.mc_registered: Dict[str, MicroController] = {}

        # Asociaciones PET {pet_num: PETAssociation}
        self.pet_associations: Dict[int, PETAssociation] = {}

        # Macros universales {macro_name: Macro}
        self.macros: Dict[str, Macro] = {}

        # Inicializar asociaciones PET (10 PET scanners)
        for i in range(1, 11):
            self.pet_associations[i] = PETAssociation(pet_num=i)

    # ==================== Microcontroladores ====================

    def register_mc(self, mc: MicroController) -> None:
        """
        Registra un microcontrolador.

        Args:
            mc: Instancia de MicroController a registrar
        """
        self.mc_registered[mc.mac_source] = mc
        if self.database:
            self._save_to_db()

    def unregister_mc(self, mac_source: str) -> bool:
        """
        Desregistra un microcontrolador.

        Args:
            mac_source: MAC de origen del microcontrolador

        Returns:
            True si se eliminó exitosamente, False si no existía
        """
        if mac_source in self.mc_registered:
            del self.mc_registered[mac_source]

            # Limpiar asociaciones PET que usen este MC
            mc_destiny = None
            for pet_num, assoc in self.pet_associations.items():
                # Buscar la MAC destiny del MC eliminado
                if assoc.mc_mac and assoc.mc_mac == mac_source:
                    assoc.mc_mac = None
                    assoc.enabled = False

            if self.database:
                self._save_to_db()
            return True
        return False

    def get_mc(self, mac_source: str) -> Optional[MicroController]:
        """
        Obtiene un microcontrolador registrado.

        Args:
            mac_source: MAC de origen del microcontrolador

        Returns:
            MicroController si existe, None en caso contrario
        """
        return self.mc_registered.get(mac_source)

    def get_mc_by_destiny(self, mac_destiny: str) -> Optional[MicroController]:
        """
        Obtiene un microcontrolador por su MAC de destino.

        Args:
            mac_destiny: MAC de destino del microcontrolador

        Returns:
            MicroController si existe, None en caso contrario
        """
        for mc in self.mc_registered.values():
            if mc.mac_destiny == mac_destiny:
                return mc
        return None

    def get_all_registered_mcs(self) -> List[MicroController]:
        """
        Obtiene lista de todos los microcontroladores registrados.

        Returns:
            Lista de MicroController
        """
        return list(self.mc_registered.values())

    def update_mc_available(self, available: Dict[str, str]) -> None:
        """
        Actualiza la lista de microcontroladores disponibles.

        Args:
            available: Diccionario {mac_source: interface_name}
        """
        self.mc_available = available.copy()

    # ==================== PET Associations ====================

    def associate_pet(self, pet_num: int, mc_mac: Optional[str], enabled: bool = False) -> None:
        """
        Asocia un PET scanner con un microcontrolador.

        Args:
            pet_num: Número del PET scanner (1-10)
            mc_mac: MAC del microcontrolador (None para desasociar)
            enabled: Si el PET está habilitado
        """
        if pet_num not in self.pet_associations:
            raise ValueError(f"PET number must be between 1 and 10, got {pet_num}")

        self.pet_associations[pet_num].mc_mac = mc_mac
        self.pet_associations[pet_num].enabled = enabled

        if self.database:
            self._save_to_db()

    def get_pet_association(self, pet_num: int) -> Optional[PETAssociation]:
        """
        Obtiene la asociación de un PET scanner.

        Args:
            pet_num: Número del PET scanner

        Returns:
            PETAssociation si existe, None en caso contrario
        """
        return self.pet_associations.get(pet_num)

    def set_pet_enabled(self, pet_num: int, enabled: bool) -> None:
        """
        Establece el estado habilitado de un PET scanner.

        Args:
            pet_num: Número del PET scanner (1-10)
            enabled: Si el PET está habilitado
        """
        if pet_num not in self.pet_associations:
            raise ValueError(f"PET number must be between 1 and 10, got {pet_num}")

        self.pet_associations[pet_num].enabled = enabled

        if self.database:
            self._save_to_db()

    def get_enabled_pet_mcs(self) -> List[str]:
        """
        Obtiene lista de MACs de MCs asociados a PETs habilitados.

        Returns:
            Lista de MAC addresses
        """
        macs = []
        for assoc in self.pet_associations.values():
            if assoc.enabled and assoc.mc_mac:
                macs.append(assoc.mc_mac)
        return macs

    def get_pets_by_mc(self, mc_mac: str) -> List[int]:
        """
        Obtiene números de PET asociados a un microcontrolador.

        Args:
            mc_mac: MAC del microcontrolador

        Returns:
            Lista de números de PET
        """
        pets = []
        for pet_num, assoc in self.pet_associations.items():
            if assoc.mc_mac == mc_mac:
                pets.append(pet_num)
        return pets

    # ==================== Macros ====================

    def save_macro(self, macro: Macro, mc_mac: Optional[str] = None) -> None:
        """
        Guarda una macro.

        Args:
            macro: Instancia de Macro a guardar
            mc_mac: Si se especifica, guarda como macro del MC. Si es None, guarda como universal
        """
        if mc_mac:
            # Macro específica de MC
            mc = self.get_mc(mc_mac)
            if not mc:
                raise ValueError(f"Microcontroller {mc_mac} not found")
            mc.macros[macro.name] = macro
        else:
            # Macro universal
            self.macros[macro.name] = macro

        if self.database:
            self._save_to_db()

    def load_macro(self, name: str, mc_mac: Optional[str] = None) -> Optional[Macro]:
        """
        Carga una macro.

        Args:
            name: Nombre de la macro
            mc_mac: Si se especifica, busca en macros del MC. Si es None, busca en universales

        Returns:
            Macro si existe, None en caso contrario
        """
        if mc_mac:
            mc = self.get_mc(mc_mac)
            if mc:
                return mc.macros.get(name)
            return None
        else:
            return self.macros.get(name)

    def delete_macro(self, name: str, mc_mac: Optional[str] = None) -> bool:
        """
        Elimina una macro.

        Args:
            name: Nombre de la macro
            mc_mac: Si se especifica, elimina de macros del MC. Si es None, elimina de universales

        Returns:
            True si se eliminó exitosamente, False si no existía
        """
        deleted = False
        if mc_mac:
            mc = self.get_mc(mc_mac)
            if mc and name in mc.macros:
                del mc.macros[name]
                deleted = True
        else:
            if name in self.macros:
                del self.macros[name]
                deleted = True

        if deleted and self.database:
            self._save_to_db()

        return deleted

    def list_macros(self, mc_mac: Optional[str] = None) -> List[str]:
        """
        Lista nombres de macros disponibles.

        Args:
            mc_mac: Si se especifica, lista macros del MC. Si es None, lista universales

        Returns:
            Lista de nombres de macros
        """
        if mc_mac:
            mc = self.get_mc(mc_mac)
            if mc:
                return list(mc.macros.keys())
            return []
        else:
            return list(self.macros.keys())

    # ==================== Persistencia ====================

    def _save_to_db(self) -> None:
        """
        Guarda el estado actual en la base de datos.

        Nota: Este método requiere que self.database esté configurado.
        """
        if not self.database:
            return

        # Update individual keys to preserve other data (like macros saved via MacroManager)
        self.database.set("mc_registered", {
            mac: mc.to_dict() for mac, mc in self.mc_registered.items()
        }, auto_save=False)

        self.database.set("pet_associations", {
            str(num): assoc.to_dict() for num, assoc in self.pet_associations.items()
        }, auto_save=False)

        # Merge with existing macros in database to preserve macros saved via MacroManager
        existing_macros = self.database.get("macros", {})
        merged_macros = existing_macros.copy()
        merged_macros.update({
            name: macro.to_dict() for name, macro in self.macros.items()
        })

        self.database.set("macros", merged_macros, auto_save=False)

        # Save once at the end
        self.database.save()

    def load_from_db(self) -> None:
        """
        Carga el estado desde la base de datos.

        Nota: Este método requiere que self.database esté configurado.
        """
        if not self.database:
            return

        data = self.database.load()

        # Cargar microcontroladores registrados
        if "mc_registered" in data:
            self.mc_registered = {}
            for mac_source, mc_data in data["mc_registered"].items():
                self.mc_registered[mac_source] = MicroController.from_dict(mac_source, mc_data)

        # Cargar asociaciones PET
        if "pet_associations" in data:
            for pet_num_str, assoc_data in data["pet_associations"].items():
                pet_num = int(pet_num_str)
                self.pet_associations[pet_num] = PETAssociation.from_dict(pet_num, assoc_data)

        # Cargar macros universales
        if "macros" in data:
            self.macros = {}
            for macro_name, macro_data in data["macros"].items():
                self.macros[macro_name] = Macro.from_dict(macro_name, macro_data)

    def to_dict(self) -> dict:
        """
        Convierte todo el estado a diccionario.

        Returns:
            Diccionario con todo el estado de la aplicación
        """
        return {
            "mc_available": self.mc_available,
            "mc_registered": {
                mac: mc.to_dict() for mac, mc in self.mc_registered.items()
            },
            "pet_associations": {
                str(num): assoc.to_dict() for num, assoc in self.pet_associations.items()
            },
            "macros": {
                name: macro.to_dict() for name, macro in self.macros.items()
            }
        }
