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

# Mockup
dataframe = {
    "metadata": {
        "temperature": 36.7,
        "status": "OK",
        "datetime": datetime.now().strftime("%d:%m:%Y %H:%M:%S")
    },
    "data": {
        "luminosity": 420,
        "datetime": datetime.now().strftime("%d:%m:%Y %H:%M:%S")
    }
}

payload = json.dumps(dataframe).encode("utf-8")

# Construcción de cabecera Ethernet: [MAC_dst][MAC_src][EtherType]
eth_header = mac_to_bytes(DESTINATION_MAC) + mac_to_bytes(SOURCE_MAC) + struct.pack("!H", 0x9000)

# Frame final
frame = eth_header + payload

print("=== Data frame builded ===")
print(frame)

# Crear raw socket ligado a la interfaz de salida
sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
sock.bind((SOURCE_INTERFACE, 0))

# Enviar
sock.send(frame)
print("✅ Frame sent via", SOURCE_INTERFACE)
