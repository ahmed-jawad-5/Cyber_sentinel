from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
import time

from server.receiver import start_receiver, stop_receiver
from server.model_runner import get_latest_alerts

app = FastAPI(title="Network Anomaly Backend")

# ------------------ CORS (GUI access) ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later restrict
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ GLOBAL STATE ------------------
receiver_thread = None
receiver_running = False


# ------------------ HELPERS ------------------
def run_receiver():
    global receiver_running
    receiver_running = True
    try:
        start_receiver()
    finally:
        receiver_running = False


# ------------------ API ENDPOINTS ------------------

@app.get("/")
def root():
    return {"status": "API running"}


@app.post("/start")
def start_capture():
    global receiver_thread

    if receiver_running:
        return {"status": "already running"}

    receiver_thread = threading.Thread(
        target=run_receiver,
        daemon=True
    )
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
    return {
        "receiver_running": receiver_running
    }


@app.get("/alerts")
def alerts():
    """
    Returns anomalous packet info produced by XGBoost + RAG
    """
    return {
        "alerts": get_latest_alerts()
    }
