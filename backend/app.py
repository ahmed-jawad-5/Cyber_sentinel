import threading
import time
import webview
import uvicorn
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer
import os

# ---------------- Backend APIs ----------------
def start_receiver_api():
    uvicorn.run("server.api:app", host="127.0.0.1", port=8000, log_level="warning")

def start_sender_api():
    uvicorn.run("client.sender_api:app", host="127.0.0.1", port=8001, log_level="warning")

# ---------------- Local HTTP server for React ----------------
def serve_frontend():
    os.chdir("gui-react/dist")  # your dist folder
    PORT = 3000
    with TCPServer(("", PORT), SimpleHTTPRequestHandler) as httpd:
        print(f"[Frontend] Serving React at http://localhost:{PORT}")
        httpd.serve_forever()

# ---------------- Desktop Launcher ----------------
if __name__ == "__main__":
    threading.Thread(target=start_receiver_api, daemon=True).start()
    threading.Thread(target=start_sender_api, daemon=True).start()
    threading.Thread(target=serve_frontend, daemon=True).start()

    # Wait for servers to start
    time.sleep(2)

    # Launch desktop window pointing to local HTTP server
    webview.create_window(
        title="Cyber-Sentinel Desktop App",
        url="http://localhost:3000",
        width=1400,
        height=900
    )
    webview.start()
