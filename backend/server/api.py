# server/api.py
from fastapi import FastAPI
from server.csv_store import get_packet_by_index
from server.rag_service import run_rag_on_packet

app = FastAPI()

@app.post("/explain/{row_index}")
def explain_packet(row_index: int):
    """
    Run RAG explanation for a specific packet row
    """
    packet = get_packet_by_index(row_index)
    explanation = run_rag_on_packet(packet)
    return {"explanation": explanation}
