import csv

CSV_PATH = "results.csv"

def get_packet_by_index(index: int) -> dict:
    with open(CSV_PATH) as f:
        rows = list(csv.DictReader(f))
    return rows[index]
