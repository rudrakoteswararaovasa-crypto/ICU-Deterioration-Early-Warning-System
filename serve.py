"""
Unified Dual Server Launcher for ICU Early-Warning System
Launches:
 - Web Dashboard Server on http://localhost:3000
 - FastAPI REST Backend API on http://localhost:8000
"""

import os
import sys
import threading
import http.server
import socketserver
import uvicorn

def start_web_server():
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web'))
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("0.0.0.0", 3000), handler) as httpd:
        print("[Web Server] Dashboard live at http://localhost:3000")
        httpd.serve_forever()

def start_api_server():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app_api import app
    print("[API Server] REST API live at http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    print("=" * 60)
    print("  Launching ICU Deterioration System Servers")
    print("  - Web Dashboard: http://localhost:3000")
    print("  - REST API:       http://localhost:8000")
    print("=" * 60)
    
    # Run Web Server in background thread
    t_web = threading.Thread(target=start_web_server, daemon=True)
    t_web.start()

    # Run API Server in main thread
    start_api_server()
