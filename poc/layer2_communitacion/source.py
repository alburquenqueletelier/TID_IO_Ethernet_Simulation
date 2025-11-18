import socket
import struct
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

SOURCE_INTERFACE = os.getenv("SOURCE_INTERFACE")
SOURCE_MAC = os.getenv("SOURCE_MAC")
DESTINATION_MAC = os.getenv("DESTINATION_MAC")

# Función para convertir string "aa:bb:cc:dd:ee:ff" -> bytes
def mac_to_bytes(mac):
    return bytes.fromhex(mac.replace(":", ""))

## Falta averiguar que es 00:07:00:00:00:00:02:03 ## 
## 00:07 ¿es el protocolo etherType o custom?
payload_base = bytes.fromhex("00:07:00:00:00:00:02:03".replace(":", ""))
appendix_dict = {
    "X_00_CPU": b"00",
    "X_02_TestTrigger": b"02",
    "X_03_RO_Single": b"03",
    "X_04_RO_ON": b"04",
    "X_05_RO_OFF": b"05",
    "X_08_DIAG_": b"08",
    "X_09_DIAG_DIS": b"09",
    "X_F9_TTrig_Global": b"F9",
    "X_FA_TTrig_Local": b"FA",
    "X_FB_TTrig_Auto_EN": b"FB",
    "X_FC_TTrig_Auto_DIS": b"FC",
    "X_FF_Reset": b"FF",
    "X_20_PwrDwnb_TOP_ON": b"20",
    "X_21_PwrDwnb_TOP_OFF": b"21",
    "X_22_PwrDwnb_BOT_ON": b"22",
    "X_23_PwrDwnb_BOT_OFF": b"23",
    "X_24_PwrEN_2V4A_ON": b"24",
    "X_25_PwrEN_2V4A_OFF": b"25",
    "X_26_PwrEN_2V4D_ON": b"26",
    "X_27_PwrEN_2V4D_OFF": b"27",
    "X_28_PwrEN_3V1_ON": b"28",
    "X_29_PwrEN_3V1_OFF": b"29",
    "X_2A_PwrEN_1V8A_ON": b"2A",
    "X_2B_PwrEN_1V8A_OFF": b"2B",
    "X_E0_FanSpeed0_Low": b"E0",
    "X_E1_FanSpeed0_High": b"E1",
    "X_E2_FanSpeed1_Low": b"E2",
    "X_E3_FanSpeed1_High": b"E3",
}

# Construcción de cabecera Ethernet: [MAC_dst][MAC_src][EtherType]
eth_header = mac_to_bytes(DESTINATION_MAC) + mac_to_bytes(SOURCE_MAC)

# Frame final
payload = payload_base + appendix_dict["X_02_TestTrigger"] # Cambiarlo según corresponda
frame = eth_header + payload

print("=== Data frame builded ===")
print(frame)

# Crear raw socket ligado a la interfaz de salida
sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
sock.bind((SOURCE_INTERFACE, 0))

# Enviar
sock.send(frame)
print("Frame sent via", SOURCE_INTERFACE)
