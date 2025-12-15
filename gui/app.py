# server.py
import http.server
import socketserver
import threading
import webview
from pathlib import Path

PORT = 5173
DIST_DIR = Path(__file__).parent / "gui-react" / "dist"

# Serve dist folder
class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIST_DIR), **kwargs)

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at http://localhost:{PORT}")
        httpd.serve_forever()

# Start HTTP server in a separate thread
threading.Thread(target=start_server, daemon=True).start()

# Start PyWebView pointing to the local server
webview.create_window(
    "UDP Network Anomaly Detector",
    f"http://localhost:{PORT}",
    width=1400,
    height=900
)
webview.start(gui='qt')
