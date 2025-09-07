import socket
import struct
import json
import os
from dotenv import load_dotenv

load_dotenv()

DESTINATION_INTERFACE= os.getenv("DESTINATION_INTERFACE")

iface = DESTINATION_INTERFACE

sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
sock.bind((iface, 0))
bufer_size = 65535

while True:
    raw_data, addr = sock.recvfrom(bufer_size) #usar una var+ verbose

    dst_mac = raw_data[0:6].hex(":")
    src_mac = raw_data[6:12].hex(":")
    eth_type = struct.unpack("!H", raw_data[12:14])[0]
    payload = raw_data[14:]

    if eth_type == 0x9000:  # nuestro tipo "custom"
        print(f"\n=== Frame received on {iface} ===")
        print("From:", src_mac, "To:", dst_mac)
        print("Raw payload:", payload)

        try:
            decoded = json.loads(payload.decode("utf-8"))
            print("Decoded payload:", decoded)
        except Exception as e:
            print("Could not decode JSON:", e)
