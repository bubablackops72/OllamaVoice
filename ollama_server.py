#!/usr/bin/env python3
"""
OllamaVoice local server — standalone version.
Serves the web UI and handles Whisper transcription.
Compatible with Python 3.13+
"""

import os
import sys
import json
import tempfile
import re
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

SERVE_DIR    = Path(__file__).parent.resolve()
CONFIG_FILE  = SERVE_DIR / "config.json"
PORT         = 8080
WHISPER_SIZE = "base"
OLLAMA_HOST  = "http://localhost:11434"

print(f"[server] Loading Whisper model '{WHISPER_SIZE}'...")
try:
    from faster_whisper import WhisperModel
    _cpu_threads = os.cpu_count() or 16
    print(f"[server] Using {_cpu_threads} CPU threads (all cores)")
    whisper_model = WhisperModel(WHISPER_SIZE, device="cpu", compute_type="int8",
                                 cpu_threads=_cpu_threads, num_workers=1)
    print(f"[server] Whisper ready.")
except Exception as e:
    print(f"[server] ERROR loading Whisper: {e}")
    whisper_model = None

# ── Kokoro TTS (Jarvis voice) ─────────────────────────────────────
TTS_VOICE   = "bm_george"   # British male - closest to Jarvis
TTS_SPEED   = 1.0
tts_pipeline = None

print(f"[tts] Loading Kokoro ONNX TTS (voice: {TTS_VOICE})...")
try:
    from kokoro_onnx import Kokoro
    import numpy as np
    _model  = SERVE_DIR / "kokoro-v1.0.onnx"
    _voices = SERVE_DIR / "voices-v1.0.bin"
    if not _model.exists() or not _voices.exists():
        raise FileNotFoundError(f"Model files missing from {SERVE_DIR}")
    tts_pipeline = Kokoro(str(_model), str(_voices))
    print(f"[tts] Kokoro ONNX TTS ready.")
except Exception as e:
    print(f"[tts] WARNING: {e}")
    print(f"[tts] Place kokoro-v1.0.onnx and voices-v1.0.bin in: {SERVE_DIR}")



def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {"model": "llama3"}


def parse_multipart(data: bytes, boundary: str) -> dict:
    parts = {}
    boundary_bytes = f"--{boundary}".encode()
    for segment in data.split(boundary_bytes):
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
        parts[name] = {"data": body, "filename": filename_match.group(1) if filename_match else None}
    return parts


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[server] {self.address_string()} - {fmt % args}")

    def send_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200); self.send_cors(); self.end_headers()

    def do_GET(self):
        path = self.path.split("?")[0].lstrip("/")

        # Config endpoint
        if path == "config":
            cfg  = load_config()
            body = json.dumps({
                "model":       cfg.get("model", "llama3"),
                "ollama_host": OLLAMA_HOST,
            }).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_cors(); self.end_headers(); self.wfile.write(body)
            return

        if path == "":
            path = "ollama-voice-chat.html"
        file_path = SERVE_DIR / path
        if not file_path.exists() or not file_path.is_file():
            self.send_response(404); self.end_headers()
            self.wfile.write(b"Not found"); return

        ext  = file_path.suffix.lower()
        mime = {".html":"text/html",".js":"application/javascript",
                ".css":"text/css",".png":"image/png",".ico":"image/x-icon"
                }.get(ext,"application/octet-stream")
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_cors(); self.end_headers(); self.wfile.write(data)

    def do_POST(self):
        # ── /speak endpoint — Kokoro TTS → WAV audio ────────────
        if self.path == "/speak":
            if tts_pipeline is None:
                self._json_error("TTS not available"); return
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body)
                text = data.get("text", "").strip()
                if not text:
                    self._json_error("No text provided"); return

                import io
                import soundfile as sf
                import numpy as np

                # Generate audio via kokoro-onnx
                samples, sample_rate = tts_pipeline.create(
                    text, voice=TTS_VOICE, speed=TTS_SPEED, lang="en-gb"
                )

                # Write to WAV in memory
                buf = io.BytesIO()
                sf.write(buf, samples, sample_rate, format="WAV")
                wav_bytes = buf.getvalue()

                self.send_response(200)
                self.send_header("Content-Type", "audio/wav")
                self.send_header("Content-Length", str(len(wav_bytes)))
                self.send_cors()
                self.end_headers()
                self.wfile.write(wav_bytes)
                print(f"[tts] Spoke {len(text)} chars ({len(audio_data)/sample_rate:.1f}s audio)")
            except Exception as e:
                print(f"[tts] Error: {e}")
                self._json_error(str(e))
            return

        if self.path != "/transcribe":
            self.send_response(404); self.end_headers(); return
        if whisper_model is None:
            self._json_error("Whisper model not loaded"); return

        content_type   = self.headers.get("Content-Type", "")
        content_length = int(self.headers.get("Content-Length", 0))
        raw_body       = self.rfile.read(content_length)
        audio_data     = None
        filename       = "recording.webm"

        if "multipart/form-data" in content_type:
            bm = re.search(r"boundary=([^\s;]+)", content_type)
            if bm:
                parts = parse_multipart(raw_body, bm.group(1).strip('"'))
                if "file" in parts:
                    audio_data = parts["file"]["data"]
                    filename   = parts["file"]["filename"] or filename
        else:
            audio_data = raw_body

        if not audio_data:
            self._json_error("No audio data received"); return

        suffix = Path(filename).suffix or ".webm"
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio_data); tmp_path = tmp.name

        try:
            segs, _ = whisper_model.transcribe(tmp_path, beam_size=5)
            transcript = " ".join(s.text for s in segs).strip()
            print(f"[whisper] {transcript!r}")
            self._json_ok({"text": transcript})
        except Exception as e:
            print(f"[whisper] Error: {e}"); self._json_error(str(e))
        finally:
            try: os.unlink(tmp_path)
            except: pass

    def _json_ok(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self.send_cors(); self.end_headers(); self.wfile.write(body)

    def _json_error(self, msg):
        body = json.dumps({"error":msg}).encode()
        self.send_response(500)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(body)))
        self.send_cors(); self.end_headers(); self.wfile.write(body)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[server] Serving on http://localhost:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[server] Stopped.")
