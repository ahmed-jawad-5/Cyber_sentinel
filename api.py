# api.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading

from server.receiver import start_receiver, stop_receiver
from server.model_runner import ModelRunner
from server.rag_runner import RAGRunner

app = FastAPI(title="Network Anomaly Backend")

# ------------------ CORS ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ GLOBAL STATE ------------------
receiver_thread = None
receiver_running = False
alerts = []

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
        start_receiver()
    finally:
        receiver_running = False

def get_latest_alerts():
    """
    Collect latest anomalies from CSV (or memory) and enrich with RAG explanations.
    """
    import csv
    latest_alerts = []

    try:
        with open("results.csv", "r") as f:
            reader = list(csv.DictReader(f))
            # Filter last 10 anomalies
            anomalies = [r for r in reader if r["label"] == "anomaly"][-10:]

            for a in anomalies:
                query = ", ".join([f"{k}: {v}" for k, v in a.items()])
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

    if receiver_running:
        return {"status": "already running"}

    receiver_thread = threading.Thread(target=run_receiver, daemon=True)
    receiver_thread.start()

    return {"status": "receiver started"}

@app.post("/stop")
def stop_capture():
    if not receiver_running:
        return {"status": "not running"}

    stop_receiver()
    return {"status": "receiver stopping"}

@app.get("/status")
def status():
    return {"receiver_running": receiver_running}

@app.get("/alerts")
def get_alerts():
    """
    Returns recent anomalies enriched with RAG explanation.
    """
    return {"alerts": get_latest_alerts()}
