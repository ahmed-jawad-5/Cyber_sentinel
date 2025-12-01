from scapy.all import IP, UDP, Raw
import socket
import json
import random
import time
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SERVER_IP = "10.5.40.102"
SERVER_PORT = 9000

def generate_packet():
    """Generate normal or anomalous packets."""

    is_anomaly = random.random() < 0.3  # 30% anomaly

    if not is_anomaly:
        # NORMAL PACKET
        src_ip = f"192.168.1.{random.randint(2, 254)}"
        dst_ip = SERVER_IP
        sport = random.randint(1024, 65535)
        dport = SERVER_PORT
        payload = "normal_data_" + str(random.randint(1000, 9999))
    else:
        # ANOMALOUS PACKET
        src_ip = f"10.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        dst_ip = SERVER_IP
        sport = random.choice([0, 65000, 9999])     # weird ports
        dport = random.choice([1, 2, 3, 9999])      # suspicious low ports
        payload = "ANOMALY_" + "X" * random.randint(50, 300)  # large payload

    pkt = IP(src=src_ip, dst=dst_ip) / UDP(sport=sport, dport=dport) / Raw(load=payload)

    print("\n[DEBUG] Generated Packet:")
    print(f"  SRC IP  : {src_ip}")
    print(f"  DST IP  : {dst_ip}")
    print(f"  SPORT   : {sport}")
    print(f"  DPORT   : {dport}")
    print(f"  Payload : {payload[:30]}...")
    print(f"  Anomaly?: {is_anomaly}")

    return pkt, is_anomaly


def packet_to_json(pkt, is_anomaly):
    return {
        "src_ip": pkt[IP].src,
        "dst_ip": pkt[IP].dst,
        "src_port": pkt[UDP].sport,
        "dst_port": pkt[UDP].dport,
        "payload_size": len(pkt[Raw].load),
        "is_anomaly": is_anomaly
    }


print(f"[INFO] Connecting to server {SERVER_IP}:{SERVER_PORT}...")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print("[INFO] Connected!")

while True:
    pkt, is_anomaly = generate_packet()
    data_dict = packet_to_json(pkt, is_anomaly)

    json_data = json.dumps(data_dict).encode()

    print(f"[INFO] Sending packet → {data_dict}")

    sock.sendto(json_data, (SERVER_IP, SERVER_PORT))
    time.sleep(1)
