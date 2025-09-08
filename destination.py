import socket
import struct
import json
import os
from dotenv import load_dotenv

load_dotenv()

DESTINATION_INTERFACE= os.getenv("DESTINATION_INTERFACE")

iface = DESTINATION_INTERFACE

appendix_dict = {
    b"00": "X_00_CPU",
    b"02": "X_02_TestTrigger",
    b"03": "X_03_RO_Single",
    b"04": "X_04_RO_ON",
    b"05": "X_05_RO_OFF",
    b"08": "X_08_DIAG_",
    b"09": "X_09_DIAG_DIS",
    b"F9": "X_F9_TTrig_Global",
    b"FA": "X_FA_TTrig_Local",
    b"FB": "X_FB_TTrig_Auto_EN",
    b"FC": "X_FC_TTrig_Auto_DIS",
    b"FF": "X_FF_Reset",
    b"20": "X_20_PwrDwnb_TOP_ON",
    b"21": "X_21_PwrDwnb_TOP_OFF",
    b"22": "X_22_PwrDwnb_BOT_ON",
    b"23": "X_23_PwrDwnb_BOT_OFF",
    b"24": "X_24_PwrEN_2V4A_ON",
    b"25": "X_25_PwrEN_2V4A_OFF",
    b"26": "X_26_PwrEN_2V4D_ON",
    b"27": "X_27_PwrEN_2V4D_OFF",
    b"28": "X_28_PwrEN_3V1_ON",
    b"29": "X_29_PwrEN_3V1_OFF",
    b"2A": "X_2A_PwrEN_1V8A_ON",
    b"2B": "X_2B_PwrEN_1V8A_OFF",
    b"E0": "X_E0_FanSpeed0_Low",
    b"E1": "X_E1_FanSpeed0_High",
    b"E2": "X_E2_FanSpeed1_Low",
    b"E3": "X_E3_FanSpeed1_High",
}

sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(3))
sock.bind((iface, 0))
bufer_size = 65535 # n° arbitrario en bytes

while True:
    raw_data, addr = sock.recvfrom(bufer_size) 

    dst_mac = raw_data[0:6].hex(":")
    src_mac = raw_data[6:12].hex(":")
    eth_type = struct.unpack("!H", raw_data[12:14])[0]
    payload = raw_data[14:22]

    if eth_type == 0x0007:  # nuestro tipo "custom"
        print(f"\n=== Frame received on {iface} ===")
        print("From:", src_mac, "To:", dst_mac)
        print("Raw payload:", payload)
        print("Payload Parse")
        parse_payload = {
            "length": payload[0:2],
            # "unknowBytes": payload[2:6], #falta averiguar que es
            # "counter_frame": payload[6:10],
            # "position_ID": payload[10:11], # falta averiguar que es
            # "counter": payload[11:12], # falta averiguar que es 
            "appendix_bytes": payload[6:8],
            "appendix_name": appendix_dict[payload[6:8]] 
            # "appendix_name": appendix_dict[payload[12:13]] 
        }
        print(parse_payload)

    else:
        print("There isn't an etherType frame")
