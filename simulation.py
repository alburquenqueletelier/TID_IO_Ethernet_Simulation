from scapy.all import Ether, Raw, sendp
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

SOURCE_INTERFACE = os.getenv("SOURCE_INTERFACE")
SOURCE_MAC = os.getenv("SOURCE_MAC")
DESTINATION_MAC= os.getenv("DESTINATION_MAC")

"""
Simulated data frames from one device to another. 
This is possible because the network card has different 
MAC addresses for each interface.
"""

# Mockup
dataframe = {
    "metadata": {
        "temperature": 36.7,  # temperatura en °C
        "status": "OK",
        "datetime": datetime.now().strftime("%d:%m:%Y %H:%M:%S")
    },
    "data": {
        "luminosity": 420,  # valor ficticio en lux
        "datetime": datetime.now().strftime("%d:%m:%Y %H:%M:%S")
    }
}

payload = json.dumps(dataframe).encode("utf-8")
frame = Ether(dst=DESTINATION_MAC, src=SOURCE_MAC, type=0x9000) / Raw(load=payload)

print("=== Data frame builded ===")
frame.show()

sendp(frame, iface=SOURCE_INTERFACE, verbose=False) ## Use loop and count to send more than 1 packet per script executed.
