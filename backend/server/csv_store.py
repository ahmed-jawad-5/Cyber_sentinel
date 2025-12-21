import csv
import os

# Must match the path used in server/receiver.py
_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_OUTPUT_DIR = os.path.join(_BACKEND_ROOT, "output")
CSV_PATH = os.path.join(_OUTPUT_DIR, "results.csv")

def get_packet_by_index(index: int) -> dict:
    with open(CSV_PATH) as f:
        rows = list(csv.DictReader(f))
    return rows[index]
