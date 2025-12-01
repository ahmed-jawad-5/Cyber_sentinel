import socket
import json
import time
from generator.packet_generator import PacketGenerator
from capture.feature_extractor import FeatureExtractor

# =========================
# Configuration
# =========================
SERVER_IP = "192.168.223.103"  # Replace with your server IP
SERVER_PORT = 9000           # Replace with your server port
NUM_FLOWS = 50               # How many flows to send
DELAY_BETWEEN = 0.5          # Seconds between flows

# =========================
# Initialize components
# =========================
gen = PacketGenerator(dst_ip=SERVER_IP)
extractor = FeatureExtractor()

# =========================
# Connect to server
# =========================
print(f"[INFO] Connecting to server {SERVER_IP}:{SERVER_PORT}...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((SERVER_IP, SERVER_PORT))
print("[INFO] Connected!")

# =========================
# Send flows
# =========================
for i in range(1, NUM_FLOWS + 1):
    # Generate a packet (normal or anomalous)
    pkt = gen.generate_packet()

    # Extract features for sending (34 features)
    flow_features = extractor.extract({
        "src_ip": pkt[0][1].src,
        "dst_ip": pkt[0][1].dst,
        "src_port": pkt[0][2].sport if hasattr(pkt[0][2], "sport") else 0,
        "dst_port": pkt[0][2].dport if hasattr(pkt[0][2], "dport") else 0,
        "proto": 6 if pkt.haslayer("TCP") else 17,
        "state": 1,
        "sbytes": len(pkt),
        "dbytes": len(pkt),
        "sttl": pkt[0][1].ttl,
        "dttl": pkt[0][1].ttl,
        "sloss": 0,
        "service": 0,
        "Sload": len(pkt),
        "swin": 0,
        "dwin": 0,
        "stcpb": 0,
        "dtcpb": 0,
        "smeansz": len(pkt),
        "dmeansz": len(pkt),
        "res_bdy_len": 0,
        "Sjit": 0,
        "Sintpkt": 0,
        "Dintpkt": 0,
        "tcprtt": 0,
        "synack": 0,
        "ackdat": 0,
        "is_sm_ips_ports": 0,
        "ct_state_ttl": 0,
        "ct_flw_http_mthd": 0,
        "is_ftp_login": 0,
        "ct_ftp_cmd": 0,
        "ct_srv_src": 0,
        "ct_srv_dst": 0,
        "ct_dst_ltm": 0,
        "ct_src_ltm": 0,
        "ct_src_dport_ltm": 0,
        "ct_dst_sport_ltm": 0,
        "ct_dst_src_ltm": 0
    })

    # Send JSON over TCP
    try:
        sock.sendall(json.dumps(flow_features).encode() + b"\n")
        print(f"[INFO] Sent flow {i}/{NUM_FLOWS}: src={flow_features['src_ip']} dst={flow_features['dst_ip']} anomaly={pkt.haslayer('Raw') and len(pkt['Raw'])>100}")
    except Exception as e:
        print(f"[ERROR] Failed to send flow {i}: {e}")

    time.sleep(DELAY_BETWEEN)

print("[INFO] Finished sending flows. Closing connection.")
sock.close()
