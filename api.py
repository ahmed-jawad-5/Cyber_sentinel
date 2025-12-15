# api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import csv

from server.receiver import start_server  # <- use start_server instead
from server.model_runner import ModelRunner
from server.rag_runner import RAGRunner

app = FastAPI(title="Network Anomaly Backend")

# ------------------ CORS ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ GLOBAL STATE ------------------
receiver_thread = None
receiver_running = False

# Initialize RAG runner and model
model_runner = ModelRunner(
    model_path="models/XGBoost_model.pkl",
    scaler_path="models/scaler.save"
)
rag_runner = RAGRunner()

# ------------------ HELPERS ------------------
def run_receiver():
    global receiver_running
    receiver_running = True
    try:
        start_server()
    finally:
        receiver_running = False

def get_latest_alerts():
    """
    Collect latest anomalies from CSV (or memory) and enrich with RAG explanations.
    """
    latest_alerts = []

    try:
        with open("results.csv", "r") as f:
            reader = list(csv.DictReader(f))
            # Filter last 10 anomalies
            anomalies = [r for r in reader if r.get("label") != "normal"][-10:]

            for a in anomalies:
                query = ", ".join([f"{k}: {v}" for k, v in a.items()])
                # Build a minimal RAG prompt; no retrieved docs needed here
                explanation = rag_runner.build_prompt_with_context(query, [])
                latest_alerts.append({
                    "flow": a,
                    "rag_prompt": explanation
                })
    except FileNotFoundError:
        pass

    return latest_alerts

# ------------------ API ENDPOINTS ------------------
@app.get("/")
def root():
    return {"status": "API running"}

@app.post("/start")
def start_capture():
    global receiver_thread

    if receiver_thread and receiver_thread.is_alive():
        return {"status": "already running"}

    receiver_thread = threading.Thread(target=run_receiver, daemon=True)
    receiver_thread.start()

    return {"status": "receiver started"}

@app.post("/stop")
def stop_capture():
    # Currently no stop function in receiver.py
    return {"status": "stop not implemented; restart server to stop"}

@app.get("/status")
def status():
    alive = receiver_thread.is_alive() if receiver_thread else False
    return {"receiver_running": alive}

@app.get("/alerts")
def get_alerts():
    """
    Returns recent anomalies enriched with RAG explanation.
    """
    return {"alerts": get_latest_alerts()}
