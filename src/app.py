#!/usr/bin/env python3
"""
VoidChat — Flask Web Frontend (src/app.py)
Minimal, lightweight, wireframe-inspired UI.
"""

import os
import sys
import json
import uuid
import time
import queue
import threading
import tempfile
import webbrowser
from typing import Optional, Dict, Any

# ── Path bootstrap ──────────────────────────────────────────────
# We are in src/, so the project root is one directory up.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _ROOT)

from flask import Flask, render_template, request, jsonify, Response, send_from_directory
from src.main import VoidChatOrchestrator

# Point Flask to the templates/static folders inside the ui/ directory
_TEMPLATE_DIR = os.path.join(_ROOT, "ui", "templates")
_STATIC_DIR = os.path.join(_ROOT, "ui", "static")

app = Flask(__name__, template_folder=_TEMPLATE_DIR, static_folder=_STATIC_DIR)

class State:
    def __init__(self):
        self.orchestrator: Optional[VoidChatOrchestrator] = None
        self.user_config: Dict[str, Any] = {}
        self.event_queue: queue.Queue = queue.Queue()

state = State()

def load_user_config() -> Optional[dict]:
    data_dir = os.path.join(_ROOT, "data")
    config_path = os.path.join(data_dir, "user_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def init_backend(config: dict):
    state.user_config = config
    if not state.orchestrator:
        state.orchestrator = VoidChatOrchestrator(username=config["username"], peer_id=config["peer_id"])
        state.orchestrator.set_ui_event_callback(ui_event_callback)
        def _run_backend():
            try: state.orchestrator.start()
            except Exception as e: print(f"[FATAL] Backend failed: {e}")
        threading.Thread(target=_run_backend, daemon=True).start()

def ui_event_callback(event_type: str, data: dict) -> bool:
    state.event_queue.put((event_type, data))
    return False

@app.route("/")
def index():
    config = load_user_config()
    if not config:
        return render_template("login.html")
    init_backend(config)
    return render_template("index.html", username=config["username"], peer_id=config["peer_id"])

@app.route("/setup", methods=["POST"])
def setup():
    alias = request.json.get("alias", "").strip()
    if not alias:
        return jsonify({"error": "Alias cannot be empty"}), 400
    config = {"peer_id": str(uuid.uuid4()), "username": alias}
    data_dir = os.path.join(_ROOT, "data")
    os.makedirs(data_dir, exist_ok=True)
    config_path = os.path.join(data_dir, "user_config.json")
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)
    init_backend(config)
    return jsonify({"success": True})

@app.route("/api/peers")
def api_peers():
    if not state.orchestrator: return jsonify([])
    return jsonify(list(state.orchestrator.get_online_peers().values()))

@app.route("/api/history/<peer_id>")
def api_history(peer_id):
    if not state.orchestrator: return jsonify([])
    return jsonify(state.orchestrator.get_chat_history(peer_id))

@app.route("/api/send", methods=["POST"])
def api_send():
    if not state.orchestrator: return jsonify({"error": "Backend not ready"}), 500
    data = request.json
    ok = state.orchestrator.transmit_text_message(data["ip"], data["peer_id"], data["text"])
    return jsonify({"success": ok})

@app.route("/api/connect", methods=["POST"])
def api_connect():
    if not state.orchestrator: return jsonify({"error": "Backend not ready"}), 500
    data = request.json
    try:
        state.orchestrator.send_connection_request(data["ip"], data["peer_id"])
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": "Peer unreachable or socket closed"}), 500

@app.route("/api/accept_connection", methods=["POST"])
def api_accept_conn():
    if not state.orchestrator: return jsonify({"error": "Backend not ready"}), 500
    data = request.json
    state.orchestrator.accept_connection_request(data["peer_id"], data["username"], data["ip"])
    return jsonify({"success": True})

@app.route("/api/accept_file", methods=["POST"])
def api_accept_file():
    if not state.orchestrator: return jsonify({"error": "Backend not ready"}), 500
    data = request.json
    state.orchestrator.accept_file_request(data["ip"], data["session_id"])
    return jsonify({"success": True})

@app.route("/api/upload", methods=["POST"])
def api_upload():
    if not state.orchestrator: return jsonify({"error": "Backend not ready"}), 500
    ip = request.args.get("ip")
    peer_id = request.args.get("peer_id")
    file = request.files.get("file")
    if not file: return jsonify({"error": "No file received"}), 400
    
    tmp_path = os.path.join(tempfile.gettempdir(), file.filename)
    file.save(tmp_path)
    
    try:
        state.orchestrator.send_file_request(ip, peer_id, tmp_path)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/downloads/<path:filename>')
def download_file(filename):
    downloads_dir = os.path.join(_ROOT, 'downloads')
    os.makedirs(downloads_dir, exist_ok=True)
    return send_from_directory(downloads_dir, filename, as_attachment=False)

@app.route("/api/events")
def api_events():
    def event_stream():
        while True:
            try:
                etype, edata = state.event_queue.get(timeout=15)
                payload = json.dumps({"type": etype, "data": edata})
                yield f"data: {payload}\n\n"
            except queue.Empty:
                yield ": ping\n\n"
    return Response(event_stream(), mimetype="text/event-stream")

def open_browser():
    # Wait for the server to start, then open the browser
    time.sleep(1.5)
    webbrowser.open_new("http://127.0.0.1:8888")

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("   VoidChat Flask UI starting on http://127.0.0.1:8888")
    print("=" * 50 + "\n")
    
    # Start the browser opener in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    app.run(host="0.0.0.0", port=8888, threaded=True, debug=False)