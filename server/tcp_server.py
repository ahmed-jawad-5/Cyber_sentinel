# server/tcp_server.py
import socket
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import threading
import json
import csv
import os
from utils.logger import get_logger
from config.settings import OUTPUT_CSV

logger = get_logger("TCPServer")

FEATURES = [
    'proto','state','sbytes','dbytes','sttl','dttl','sloss','service',
    'Sload','swin','dwin','stcpb','dtcpb','smeansz','dmeansz','res_bdy_len',
    'Sjit','Sintpkt','Dintpkt','tcprtt','synack','ackdat','is_sm_ips_ports',
    'ct_state_ttl','ct_flw_http_mthd','is_ftp_login','ct_ftp_cmd','ct_srv_src',
    'ct_srv_dst','ct_dst_ltm','ct_src_ltm','ct_src_dport_ltm','ct_dst_sport_ltm',
    'ct_dst_src_ltm'
]

HOST = "0.0.0.0"
PORT = 9000
os.makedirs(os.path.dirname(OUTPUT_CSV) or ".", exist_ok=True)

# Ensure CSV header exists
if not os.path.exists(OUTPUT_CSV):
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(FEATURES + ["_flow_key_src","_flow_key_dst","_flow_key_sport","_flow_key_dport","_flow_key_proto"])

def handle_connection(conn, addr):
    logger.info(f"Client connected: {addr}")
    buf = ""
    try:
        with conn:
            while True:
                data = conn.recv(4096)
                if not data:
                    logger.info(f"Client disconnected: {addr}")
                    break
                buf += data.decode("utf-8", errors="ignore")
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning("Received invalid JSON line, skipping")
                        continue
                    # write row to CSV
                    row = [obj.get(k) for k in FEATURES]
                    fk = obj.get("_flow_key", {})
                    row += [fk.get("src"), fk.get("dst"), fk.get("sport"), fk.get("dport"), fk.get("proto")]
                    with open(OUTPUT_CSV, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow(row)
                    logger.info("Logged feature row to CSV")
    except Exception:
        logger.exception("Connection handler error")

def start_server(host=HOST, port=PORT):
    logger.info(f"Starting TCP server on {host}:{port}")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=handle_connection, args=(conn, addr), daemon=True)
            t.start()

if __name__ == "__main__":
    start_server()
