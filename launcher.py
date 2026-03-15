#!/usr/bin/env python3
"""
Ollama Voice Assistant Launcher
- Starts Docker/Ollama container
- Runs local Whisper transcription server
- Opens browser UI
- System tray icon to quit
"""

import os
import sys
import json
import re
import time
import tempfile
import threading
import subprocess
import webbrowser
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── Embedded HTML ────────────────────────────────────────────────
HTML_FILE = Path(__file__).parent / "ollama-voice-chat.html"

# ── Config ───────────────────────────────────────────────────────
DOCKER_CONTEXT  = "default"
OLLAMA_HOST     = "http://localhost:11434"
CHAT_MODEL      = "llama3"
PORT            = 8080
WHISPER_MODEL   = "base"
SETUP_FLAG      = Path(__file__).parent / ".ollama_setup_done"

# ── Globals ──────────────────────────────────────────────────────
whisper_model   = None
http_server     = None
tray_icon       = None

# ================================================================
#  WHISPER SERVER
# ================================================================

def load_whisper():
    global whisper_model
    print(f"[whisper] Loading model '{WHISPER_MODEL}'...")
    try:
        from faster_whisper import WhisperModel
        whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        print(f"[whisper] Model ready.")
    except Exception as e:
        print(f"[whisper] ERROR: {e}")


def parse_multipart(data: bytes, boundary: str) -> dict:
    parts = {}
    boundary_bytes = f"--{boundary}".encode()
    segments = data.split(boundary_bytes)
    for segment in segments:
        if b"Content-Disposition" not in segment:
            continue
        try:
            header_section, body = segment.split(b"\r\n\r\n", 1)
        except ValueError:
            continue
        if body.endswith(b"\r\n"):
            body = body[:-2]
        headers_raw = header_section.decode(errors="replace")
        name_match = re.search(r'name="([^"]+)"', headers_raw)
        if not name_match:
            continue
        name = name_match.group(1)
        filename_match = re.search(r'filename="([^"]+)"', headers_raw)
        filename = filename_match.group(1) if filename_match else None
        parts[name] = {"data": body, "filename": filename}
    return parts


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[server] {self.address_string()} - {format % args}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].lstrip("/")
        if path == "":
            path = "ollama-voice-chat.html"

        serve_dir = Path(__file__).parent
        file_path = serve_dir / path

        if not file_path.exists() or not file_path.is_file():
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not found")
            return

        ext = file_path.suffix.lower()
        mime = {
            ".html": "text/html",
            ".js":   "application/javascript",
            ".css":  "text/css",
            ".png":  "image/png",
            ".ico":  "image/x-icon",
        }.get(ext, "application/octet-stream")

        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_cors()
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        if self.path != "/transcribe":
            self.send_response(404)
            self.end_headers()
            return

        if whisper_model is None:
            self._json_error("Whisper model not loaded yet — please wait")
            return

        content_type   = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body       = self.rfile.read(content_length)

        audio_data = None
        filename   = "recording.webm"

        if "multipart/form-data" in content_type:
            boundary_match = re.search(r"boundary=([^\s;]+)", content_type)
            if boundary_match:
                boundary   = boundary_match.group(1).strip('"')
                parts      = parse_multipart(raw_body, boundary)
                if "file" in parts:
                    audio_data = parts["file"]["data"]
                    filename   = parts["file"]["filename"] or filename
        else:
            audio_data = raw_body

        if not audio_data:
            self._json_error("No audio data received")
            return

        suffix = Path(filename).suffix or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_data)
            tmp_path = tmp.name

        try:
            segments, _ = whisper_model.transcribe(tmp_path, beam_size=5)
            transcript  = " ".join(seg.text for seg in segments).strip()
            print(f"[whisper] Transcript: {transcript!r}")
            self._json_ok({"text": transcript})
        except Exception as e:
            print(f"[whisper] Error: {e}")
            self._json_error(str(e))
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    def _json_ok(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)

    def _json_error(self, msg):
        body = json.dumps({"error": msg}).encode()
        self.send_response(500)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors()
        self.end_headers()
        self.wfile.write(body)


def run_http_server():
    global http_server
    http_server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[server] Listening on http://localhost:{PORT}")
    http_server.serve_forever()


# ================================================================
#  DOCKER / OLLAMA
# ================================================================

def docker(args, check=False):
    cmd = ["docker", "--context", DOCKER_CONTEXT] + args
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def ensure_ollama_container():
    if SETUP_FLAG.exists():
        print("[docker] Setup already done — starting existing container...")
        docker(["start", "ollama"])
        time.sleep(5)
        return

    print("[docker] First-time setup — recreating container with CORS...")
    docker(["stop", "ollama"])
    docker(["rm",   "ollama"])

    result = docker([
        "run", "-d",
        "--gpus", "all",
        "--name", "ollama",
        "-p", "11434:11434",
        "-e", "OLLAMA_ORIGINS=*",
        "-e", "OLLAMA_KEEP_ALIVE=-1",
        "-v", "ollama:/root/.ollama",
        "ollama/ollama"
    ])

    if result.returncode != 0:
        print(f"[docker] ERROR: {result.stderr}")
        sys.exit(1)

    print("[docker] Container started. Waiting for Ollama to be ready...")
    time.sleep(8)
    SETUP_FLAG.write_text("done")
    print("[docker] Setup complete.")


def launch_llama():
    print(f"[ollama] Launching {CHAT_MODEL}...")
    docker([
        "exec", "-it",
        "-e", "OLLAMA_NUM_GPU=999",
        "-e", "CUDA_VISIBLE_DEVICES=all",
        "-e", "OLLAMA_GPU_LAYERS=999",
        "-e", "OLLAMA_FLASH_ATTENTION=1",
        "-e", "OLLAMA_NUM_THREAD=1",
        "-e", "OLLAMA_NUM_PARALLEL=1",
        "-e", "OLLAMA_NUM_BATCH=512",
        "ollama", "ollama", "run", CHAT_MODEL
    ])


# ================================================================
#  SYSTEM TRAY
# ================================================================

def create_tray():
    try:
        import pystray
        from PIL import Image, ImageDraw

        # Draw a simple mic icon
        img  = Image.new("RGB", (64, 64), color=(12, 12, 14))
        draw = ImageDraw.Draw(img)
        draw.ellipse([20, 4, 44, 36], outline=(232, 255, 71), width=3)
        draw.line([32, 36, 32, 52], fill=(232, 255, 71), width=3)
        draw.line([20, 52, 44, 52], fill=(232, 255, 71), width=3)

        def on_open(icon, item):
            webbrowser.open(f"http://localhost:{PORT}/ollama-voice-chat.html")

        def on_quit(icon, item):
            print("[tray] Quitting...")
            icon.stop()
            if http_server:
                http_server.shutdown()
            docker(["stop", "ollama"])
            os._exit(0)

        menu  = pystray.Menu(
            pystray.MenuItem("Open Voice UI", on_open, default=True),
            pystray.MenuItem("Quit", on_quit),
        )
        icon  = pystray.Icon("OllamaVoice", img, "Ollama Voice", menu)
        print("[tray] System tray icon active — right-click to quit")
        icon.run()

    except ImportError:
        print("[tray] pystray/Pillow not installed — no tray icon. Close this window to quit.")
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            docker(["stop", "ollama"])
            sys.exit(0)


# ================================================================
#  MAIN
# ================================================================

if __name__ == "__main__":
    print("=" * 50)
    print("  OLLAMA VOICE ASSISTANT")
    print("=" * 50)

    # 1. Docker / Ollama
    ensure_ollama_container()

    # 2. Start HTTP + Whisper server in background threads
    threading.Thread(target=run_http_server,  daemon=True).start()
    threading.Thread(target=load_whisper,     daemon=True).start()

    # 3. Launch llama3 in background (keeps model hot)
    threading.Thread(target=launch_llama, daemon=True).start()

    # 4. Wait a moment then open browser
    time.sleep(3)
    print(f"[browser] Opening http://localhost:{PORT}/ollama-voice-chat.html")
    webbrowser.open(f"http://localhost:{PORT}/ollama-voice-chat.html")

    # 5. System tray (blocks main thread)
    create_tray()
