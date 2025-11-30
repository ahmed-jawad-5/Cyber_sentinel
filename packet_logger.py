# packet_logger.py
import csv
import os
from datetime import datetime

CSV_FILE = "received_packets.csv"

# Ensure CSV exists with header
if not os.path.exists(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "src_ip", "src_port", "raw_packet"])


def log_packet(addr, raw_bytes):
    """
    Append received packet data to CSV.
    addr = (ip, port)
    raw_bytes = bytes
    """
    timestamp = datetime.utcnow().isoformat()

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            addr[0],
            addr[1],
            raw_bytes.hex()  # store safely as hex instead of raw bytes
        ])
