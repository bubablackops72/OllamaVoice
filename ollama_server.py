#!/usr/bin/env python3
"""
Local Whisper transcription server + static file server.
Compatible with Python 3.13+ (no cgi module required).
"""

import os
import sys
import json
import tempfile
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

SERVE_DIR = Path(__file__).parent.resolve()
PORT = 8080
MODEL_SIZE = "base"  # tiny | base | small | medium | large

print(f"[server] Loading Whisper model '{MODEL_SIZE}'...")
print(f"[server] NOTE: First run downloads ~150MB model - please wait...")
try:
    from faster_whisper import WhisperModel
    whisper_model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    print(f"[server] Whisper '{MODEL_SIZE}' ready.")
except Exception as e:
    print(f"[server] ERROR loading Whisper: {e}")
    whisper_model = None


def parse_multipart(data: bytes, boundary: str) -> dict:
    """Parse multipart form data without the cgi module."""
    parts = {}
    boundary_bytes = f"--{boundary}".encode()
    segments = data.split(boundary_bytes)
    for segment in segments:
        if b"Content-Disposition" not in segment:
            continue
        # Split headers from body
        try:
            header_section, body = segment.split(b"\r\n\r\n", 1)
        except ValueError:
            continue
        # Remove trailing boundary marker
        if body.endswith(b"\r\n"):
            body = body[:-2]
        headers_raw = header_section.decode(errors="replace")
        # Extract field name
        name_match = re.search(r'name="([^"]+)"', headers_raw)
        if not name_match:
            continue
        name = name_match.group(1)
        # Extract filename if present
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

        file_path = SERVE_DIR / path
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
            self._json_error("Whisper model not loaded")
            return

        content_type = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length)

        audio_data = None
        filename = "recording.webm"

        if "multipart/form-data" in content_type:
            boundary_match = re.search(r"boundary=([^\s;]+)", content_type)
            if boundary_match:
                boundary = boundary_match.group(1).strip('"')
                parts = parse_multipart(raw_body, boundary)
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
            segments, info = whisper_model.transcribe(tmp_path, beam_size=5)
            transcript = " ".join(seg.text for seg in segments).strip()
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


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[server] Serving on http://localhost:{PORT}")
    print(f"[server] Open: http://localhost:{PORT}/ollama-voice-chat.html")
    print(f"[server] Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] Stopped.")
