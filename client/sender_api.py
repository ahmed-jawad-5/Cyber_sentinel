from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading

from client.client_sender import start_sender, stop_sender

# -------------------------------------------------
# FastAPI App
# -------------------------------------------------
app = FastAPI(title="Sender Control API")

# -------------------------------------------------
# CORS (for React / Web UI)
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # restrict later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# GLOBAL STATE
# -------------------------------------------------
sender_thread = None
sender_running = False


# -------------------------------------------------
# REQUEST MODEL
# -------------------------------------------------
class SenderConfig(BaseModel):
    host: str
    port: int
    delay: float


# -------------------------------------------------
# ROUTES
# -------------------------------------------------
@app.get("/status")
def get_status():
    return {
        "running": sender_running
    }


@app.post("/start")
def start_sender_api(cfg: SenderConfig):
    global sender_thread, sender_running

    if sender_running:
        return {
            "status": "already running"
        }

    sender_thread = threading.Thread(
        target=start_sender,
        kwargs={
            "host": cfg.host,
            "port": cfg.port,
            "delay": cfg.delay,
        },
        daemon=True,
    )
    sender_thread.start()

    sender_running = True

    return {
        "status": "started",
        "host": cfg.host,
        "port": cfg.port,
        "delay": cfg.delay,
    }


@app.post("/stop")
def stop_sender_api():
    global sender_running

    if not sender_running:
        return {
            "status": "already stopped"
        }

    stop_sender()
    sender_running = False

    return {
        "status": "stopped"
    }
