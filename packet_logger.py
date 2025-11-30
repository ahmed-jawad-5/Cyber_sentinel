# packet_logger.py
import csv
import os
from datetime import datetime

CSV_FILE = "received_packets.csv"

if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "src_ip", "src_port", "raw_hex"])


def log_packet(addr, raw_bytes):
    ts = datetime.utcnow().isoformat()

    with open(CSV_FILE, "a", newline="") as f:
        w = csv.writer(f)
        w.writerow([ts, addr[0], addr[1], raw_bytes.hex()])
