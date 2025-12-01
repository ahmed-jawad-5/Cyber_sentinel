# capture/utils_capture.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import csv
import os
from datetime import datetime
from config.settings import CAPTURED_FLOWS_CSV, ANOMALIES_CSV

# Ensure output folder exists
os.makedirs(os.path.dirname(CAPTURED_FLOWS_CSV), exist_ok=True)

# Initialize CSV files if they do not exist
def init_csv_files(feature_columns):
    if not os.path.exists(CAPTURED_FLOWS_CSV):
        with open(CAPTURED_FLOWS_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=feature_columns)
            writer.writeheader()

    if not os.path.exists(ANOMALIES_CSV):
        with open(ANOMALIES_CSV, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=feature_columns + ["anomaly_score"])
            writer.writeheader()


# Append a row to captured flows CSV
def write_flow_csv(row: dict):
    with open(CAPTURED_FLOWS_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        writer.writerow(row)


# Append anomaly to CSV
def write_anomaly_csv(row: dict, score: float):
    row_copy = row.copy()
    row_copy["anomaly_score"] = score
    with open(ANOMALIES_CSV, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row_copy.keys())
        writer.writerow(row_copy)
# capture/utils_capture.py

from scapy.layers.inet import IP, TCP, UDP

def get_5tuple(pkt):
    try:
        src_ip = pkt[IP].src if IP in pkt else None
        dst_ip = pkt[IP].dst if IP in pkt else None
        proto  = pkt[IP].proto if IP in pkt else None

        src_port = pkt[TCP].sport if TCP in pkt else (pkt[UDP].sport if UDP in pkt else None)
        dst_port = pkt[TCP].dport if TCP in pkt else (pkt[UDP].dport if UDP in pkt else None)

        return (src_ip, dst_ip, src_port, dst_port, proto)
    except Exception as e:
        logger.error(f"[get_5tuple ERROR] {e}")
        return (None, None, None, None, None)
