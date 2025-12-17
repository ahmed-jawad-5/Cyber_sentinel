import threading
import time
import webview
import uvicorn

def start_sender_api():
    # Correct import string for FastAPI sender
    uvicorn.run("client.sender_api:app", host="127.0.0.1", port=8001, log_level="warning")

def start_receiver_api():
    # Correct import string for FastAPI receiver
    uvicorn.run("server.api:app", host="127.0.0.1", port=8000, log_level="warning")

if __name__ == "__main__":
    # Start APIs in background threads
    threading.Thread(target=start_receiver_api, daemon=True).start()
    threading.Thread(target=start_sender_api, daemon=True).start()

    time.sleep(2)  # allow servers to start

    # Launch React build in PyWebView using Qt backend
    webview.create_window(
        title="Cyber-Sentinel Desktop App",
        url="gui-react/dist/index.html",
        width=1400,
        height=900
    )
    webview.start(gui='qt')  # <--- force Qt backend
