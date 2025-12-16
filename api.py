from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import threading
import time
from fastapi.encoders import jsonable_encoder

# Import your custom modules
from server.receiver import start_server
from server.rag_runner import RAGRunner

app = FastAPI(title="Cyber-Sentinel AI Backend")

# ------------------ CORS CONFIG ------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ GLOBAL STATE ------------------
latest_anomalies = []  
MAX_STORED_ALERTS = 50
alert_lock = threading.Lock()
receiver_thread = None

# Initialize RAG Runner
try:
    rag_runner = RAGRunner()
    print("[SYSTEM] RAG Runner initialized and Vector DB loaded.")
except Exception as e:
    print(f"[SYSTEM ERROR] RAG initialization failed: {e}")
    rag_runner = None

# ------------------ HELPER FUNCTIONS ------------------

def notify_new_packet(alert_data):
    """
    Callback used by receiver.py. 
    alert_data should be: {"flow": {...}, "rag_prompt": None}
    """
    with alert_lock:
        latest_anomalies.insert(0, alert_data)
        if len(latest_anomalies) > MAX_STORED_ALERTS:
            latest_anomalies.pop()

# ------------------ API ENDPOINTS ------------------

@app.get("/status")
def get_status():
    alive = receiver_thread.is_alive() if receiver_thread else False
    return {"receiver_running": alive}

@app.post("/start")
def start_capture():
    global receiver_thread
    if receiver_thread and receiver_thread.is_alive():
        return {"status": "already running"}
    
    # Start the socket receiver in a background thread
    receiver_thread = threading.Thread(
        target=start_server, 
        args=(notify_new_packet,), 
        daemon=True
    )
    receiver_thread.start()
    return {"status": "receiver started"}

@app.get("/alerts")
def get_alerts():
    with alert_lock:
        # Use jsonable_encoder to safely handle NumPy/special types
        return {"alerts": jsonable_encoder(latest_anomalies)}

@app.post("/explain/{packet_id}")
def explain_alert(packet_id: str):
    """
    Finds a packet by its String ID and generates an AI explanation.
    The 'str' type hint fixes the 422 Unprocessable Entity error.
    """
    target_alert = None
    
    # 1. Thread-safe search for the specific packet
    with alert_lock:
        for alert in latest_anomalies:
            if str(alert["flow"].get("id")) == packet_id:
                target_alert = alert
                break
    
    if not target_alert:
        return {"explanation": "Packet ID not found in current memory cache."}, 404

    # 2. Extract features for the AI
    packet_features = target_alert["flow"]
    # Create a string representation for the RAG query
    query_str = " | ".join([f"{k}: {v}" for k, v in packet_features.items() if k not in ["id", "rag_prompt"]])

    try:
        if rag_runner:
            # --- RAG LOGIC ---
            # Generate embedding for the specific packet features
            q_emb = rag_runner.emb_model.encode([query_str], convert_to_numpy=True)
            import faiss
            faiss.normalize_L2(q_emb)

            # Search Vector DB for similar historical attacks
            retrieved_docs = []
            if rag_runner.index.ntotal > 0:
                D, I = rag_runner.index.search(q_emb, rag_runner.top_k)
                retrieved_docs = [rag_runner.metadata[i] for i in I[0].tolist()]

            # Build and Generate
            prompt = rag_runner.build_prompt_with_context(query_str, retrieved_docs, detailed=True)
            explanation = rag_runner.llm.generate(prompt, max_new_tokens=500)
        else:
            explanation = "RAG Engine is currently offline."

    except Exception as e:
        print(f"[EXPLAIN ERROR]: {e}")
        explanation = f"AI Analysis failed: {str(e)}"

    # 3. Save the result back to the specific packet in the list
    with alert_lock:
        # Re-search to ensure the packet is still there before saving
        for alert in latest_anomalies:
            if str(alert["flow"].get("id")) == packet_id:
                alert["rag_prompt"] = explanation
                break

    return {"explanation": explanation}

@app.get("/")
def read_root():
    return {"message": "Cyber-Sentinel API is online"}