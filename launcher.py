#!/usr/bin/env python3
"""
OllamaVoice Launcher
- Auto-starts Docker Desktop if not running
- Shows model selector dialog
- Starts local Whisper + web server
- Opens browser UI
- System tray icon
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

APP_DIR       = Path(sys.executable).parent.resolve() if getattr(sys, 'frozen', False) else Path(__file__).parent.resolve()
_APPDATA_DIR  = Path(os.environ.get("APPDATA", str(APP_DIR))) / "OllamaVoice"
_APPDATA_DIR.mkdir(parents=True, exist_ok=True)

# ── Debug log file (always written regardless of console) ────────
import datetime
_LOG_FILE = Path(os.environ.get("TEMP", ".")) / "ollamavoice_debug.log"
def _log(msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass
CONFIG_FILE   = _APPDATA_DIR / "config.json"
HTML_FILE     = APP_DIR / "ollama-voice-chat.html"
DOCKER_CONTEXT = "default"
OLLAMA_HOST   = "http://localhost:11434"
PORT          = 8080
WHISPER_MODEL = "base"
SETUP_FLAG    = _APPDATA_DIR / ".ollama_setup_done"

DOCKER_DESKTOP_PATHS = [
    r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
    r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Docker\Docker Desktop.exe"),
]


# ================================================================
#  CPU AFFINITY HELPER (WSL2/vmmem)
# ================================================================

def set_vmmem_affinity(fraction=0.25):
    """
    Limit WSL2 CPU usage by setting processor affinity on the vmmem process.
    fraction=0.25 means use at most 25% of CPU cores.
    Returns the original affinity mask so it can be restored.
    """
    if sys.platform != "win32":
        return None
    try:
        import ctypes
        total = os.cpu_count() or 4
        allowed = max(1, int(total * fraction))
        allowed_mask = (1 << allowed) - 1
        full_mask    = (1 << total) - 1

        # Find vmmem process via tasklist
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq vmmem.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True
        )
        pids = []
        for line in result.stdout.strip().splitlines():
            parts = line.strip('"').split('","')
            if len(parts) >= 2:
                try:
                    pids.append(int(parts[1]))
                except ValueError:
                    pass

        if not pids:
            print("[cpu] vmmem not found — Docker may not be running yet")
            return None

        PROCESS_ALL_ACCESS = 0x1F0FFF
        originals = {}
        for pid in pids:
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if handle:
                old_mask = ctypes.c_ulong(0)
                sys_mask = ctypes.c_ulong(0)
                ctypes.windll.kernel32.GetProcessAffinityMask(handle, ctypes.byref(old_mask), ctypes.byref(sys_mask))
                ctypes.windll.kernel32.SetProcessAffinityMask(handle, allowed_mask)
                originals[pid] = (handle, old_mask.value)
                print(f"[cpu] vmmem PID {pid}: limited to {allowed}/{total} cores")

        return originals
    except Exception as e:
        print(f"[cpu] Could not set CPU affinity: {e}")
        return None


def restore_vmmem_affinity(originals):
    """Restore original CPU affinity on vmmem after download completes."""
    if not originals:
        return
    try:
        import ctypes
        for pid, (handle, old_mask) in originals.items():
            ctypes.windll.kernel32.SetProcessAffinityMask(handle, old_mask)
            ctypes.windll.kernel32.CloseHandle(handle)
            print(f"[cpu] vmmem PID {pid}: CPU affinity restored")
    except Exception as e:
        print(f"[cpu] Could not restore CPU affinity: {e}")

AVAILABLE_MODELS = {
    "llama3":           {"label": "Llama 3 (4.7GB)  - Fast, efficient general purpose"},
    "mistral-small:22b":{"label": "Mistral 22B (13GB) - Balanced performance"},
    "qwen2.5:32b":      {"label": "Qwen 2.5 32B (19GB) - Excellent reasoning"},
    "deepseek-r1:32b":  {"label": "DeepSeek R1 32B (19GB) - Best for coding & reasoning"},
    "gemma2:27b":       {"label": "Gemma 2 27B (16GB) - Google open model"},
}

whisper_model = None
http_server   = None


# ================================================================
#  CONFIG
# ================================================================

def load_config():
    defaults = {"model": "llama3"}
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            defaults.update(data)
        except Exception:
            pass
    return defaults


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


# ================================================================
#  DOCKER DESKTOP AUTO-START
# ================================================================

def is_docker_running():
    try:
        r = subprocess.run(
            ["docker", "--context", DOCKER_CONTEXT, "info"],
            capture_output=True, timeout=5
        )
        return r.returncode == 0
    except Exception:
        return False


def start_docker_desktop():
    print("[docker] Docker not running — attempting to start Docker Desktop...")
    docker_exe = None
    for path in DOCKER_DESKTOP_PATHS:
        if os.path.exists(path):
            docker_exe = path
            break

    if not docker_exe:
        print("[docker] Docker Desktop not found at known paths.")
        print("[docker] Please start Docker Desktop manually and relaunch.")
        input("Press Enter to exit...")
        sys.exit(1)

    subprocess.Popen([docker_exe])
    print("[docker] Waiting for Docker Desktop to start (up to 60 seconds)...")

    for i in range(60):
        time.sleep(2)
        if is_docker_running():
            print("[docker] Docker Desktop is ready.")
            return
        if i % 10 == 0:
            print(f"[docker] Still waiting... ({i*2}s)")

    print("[docker] Docker Desktop did not start in time.")
    print("[docker] Please ensure Docker Desktop is running and try again.")
    input("Press Enter to exit...")
    sys.exit(1)


def ensure_docker():
    if not is_docker_running():
        start_docker_desktop()
    else:
        print("[docker] Docker is running.")


# ================================================================
#  MODEL SELECTOR DIALOG
# ================================================================

def get_installed_models():
    """Query Ollama for which models are actually installed."""
    try:
        r = subprocess.run(
            ["docker", "--context", DOCKER_CONTEXT, "exec", "ollama", "ollama", "list"],
            capture_output=True, text=True, timeout=10
        )
        lines = r.stdout.strip().split("\n")
        installed = []
        for line in lines[1:]:  # skip header
            parts = line.split()
            if parts:
                installed.append(parts[0])
        return installed
    except Exception:
        return []


def show_model_selector(current_model):
    """Show a tkinter model selection dialog. Returns selected model name."""
    import tkinter as tk
    from tkinter import ttk, font as tkfont

    installed = get_installed_models()
    selected_model = [current_model]

    root = tk.Tk()
    root.title("OllamaVoice — Select Model")
    root.resizable(False, False)
    root.configure(bg="#0c0c0e")

    # Center window
    w, h = 480, 420
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    # Fonts
    title_font  = tkfont.Font(family="Consolas", size=13, weight="bold")
    label_font  = tkfont.Font(family="Consolas", size=10)
    button_font = tkfont.Font(family="Consolas", size=10, weight="bold")
    small_font  = tkfont.Font(family="Consolas", size=8)

    # Title
    tk.Label(root, text="VOICE // OLLAMA",
             bg="#0c0c0e", fg="#e8ff47",
             font=title_font).pack(pady=(20, 4))
    tk.Label(root, text="Select AI Model",
             bg="#0c0c0e", fg="#6e6e82",
             font=label_font).pack(pady=(0, 16))

    # Model list frame
    frame = tk.Frame(root, bg="#141418", bd=1, relief="flat",
                     highlightbackground="#2a2a32", highlightthickness=1)
    frame.pack(padx=24, fill="x")

    radio_var = tk.StringVar(value=current_model)

    for model_key, info in AVAILABLE_MODELS.items():
        is_installed = any(m.startswith(model_key.split(":")[0]) for m in installed)
        status_color = "#e8ff47" if is_installed else "#4a4a58"
        status_text  = "installed" if is_installed else "not installed"
        row_bg       = "#1a1a22" if is_installed else "#141418"

        row = tk.Frame(frame, bg=row_bg, pady=6)
        row.pack(fill="x", padx=1, pady=1)

        rb = tk.Radiobutton(
            row, variable=radio_var, value=model_key,
            bg=row_bg, activebackground=row_bg,
            fg="#d8d8e8" if is_installed else "#4a4a58",
            selectcolor="#0c0c0e",
            font=label_font,
            state="normal" if is_installed else "disabled",
            text=info["label"]
        )
        rb.pack(side="left", padx=(10, 4))

        tk.Label(row, text=f"[{status_text}]",
                 bg=row_bg, fg=status_color,
                 font=small_font).pack(side="right", padx=10)

    # Note if no models installed
    if not installed:
        tk.Label(root,
                 text="No models found.\nInstall models via the installer or run:\ndocker exec ollama ollama pull llama3",
                 bg="#0c0c0e", fg="#ff4757",
                 font=small_font, justify="center").pack(pady=10)

    # Separator
    tk.Frame(root, bg="#2a2a32", height=1).pack(fill="x", padx=24, pady=16)

    # Launch button
    def on_launch():
        selected_model[0] = radio_var.get()
        root.destroy()

    def on_quit():
        sys.exit(0)

    btn_frame = tk.Frame(root, bg="#0c0c0e")
    btn_frame.pack(pady=(0, 20))

    tk.Button(
        btn_frame, text="LAUNCH",
        bg="#e8ff47", fg="#0c0c0e",
        font=button_font,
        relief="flat", bd=0,
        padx=24, pady=8,
        cursor="hand2",
        command=on_launch
    ).pack(side="left", padx=8)

    tk.Button(
        btn_frame, text="QUIT",
        bg="#141418", fg="#6e6e82",
        font=button_font,
        relief="flat", bd=0,
        padx=24, pady=8,
        cursor="hand2",
        highlightbackground="#2a2a32",
        highlightthickness=1,
        command=on_quit
    ).pack(side="left", padx=8)

    root.protocol("WM_DELETE_WINDOW", on_quit)
    root.mainloop()

    return selected_model[0]


# ================================================================
#  OLLAMA CONTAINER
# ================================================================

def docker(args):
    cmd = ["docker", "--context", DOCKER_CONTEXT] + args
    return subprocess.run(cmd, capture_output=True, text=True)


def ensure_ollama_container():
    if SETUP_FLAG.exists():
        print("[docker] Starting existing Ollama container...")
        docker(["start", "ollama"])
        time.sleep(5)
        return

    print("[docker] First-time setup — creating Ollama container...")
    docker(["stop", "ollama"])
    docker(["rm",   "ollama"])

    result = docker([
        "run", "-d",
        "--gpus", "all",
        "--name", "ollama",
        "-p", "11434:11434",
        # Allow web UI access
        "-e", "OLLAMA_ORIGINS=*",
        "-e", "OLLAMA_KEEP_ALIVE=-1",
        # Force 100% GPU - baked into container so all sessions use it
        "-e", "OLLAMA_NUM_GPU=999",
        "-e", "OLLAMA_GPU_LAYERS=999",
        "-e", "OLLAMA_MAIN_GPU=0",
        "-e", "OLLAMA_FLASH_ATTENTION=1",
        "-e", "OLLAMA_KV_CACHE_TYPE=q8_0",
        "-v", "ollama:/root/.ollama",
        "ollama/ollama"
    ])

    if result.returncode != 0:
        print(f"[docker] ERROR: {result.stderr}")
        sys.exit(1)

    print("[docker] Container created. Waiting for Ollama to be ready...")
    time.sleep(8)
    SETUP_FLAG.write_text("done")


def launch_model(model):
    print(f"[ollama] Launching {model} (100% GPU mode)...")
    docker([
        "exec", "-it",
        # Force ALL layers onto GPU - no CPU offload
        "-e", "OLLAMA_NUM_GPU=999",
        "-e", "OLLAMA_GPU_LAYERS=999",
        "-e", "CUDA_VISIBLE_DEVICES=all",
        "-e", "OLLAMA_MAIN_GPU=0",
        # Flash attention reduces VRAM usage, helping keep all layers on GPU
        "-e", "OLLAMA_FLASH_ATTENTION=1",
        # Quantize KV cache to q8 to save VRAM (frees room for all GPU layers)
        "-e", "OLLAMA_KV_CACHE_TYPE=q8_0",
        # Use all CPU cores for fast model loading into VRAM
        "-e", f"OLLAMA_NUM_THREAD={os.cpu_count() or 16}",
        "-e", "OLLAMA_NUM_PARALLEL=1",
        "-e", "OLLAMA_NUM_BATCH=512",
        "ollama", "ollama", "run", model
    ])


# ================================================================
#  WHISPER + HTTP SERVER (imported from ollama_server.py)
# ================================================================

def load_whisper():
    global whisper_model
    print(f"[whisper] Loading model '{WHISPER_MODEL}'...")
    try:
        from faster_whisper import WhisperModel
        _cpu_threads = os.cpu_count() or 16
        print(f"[whisper] Using {_cpu_threads} CPU threads (all cores)")
        whisper_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8",
                                     cpu_threads=_cpu_threads, num_workers=1)
        print("[whisper] Model ready.")
    except Exception as e:
        print(f"[whisper] ERROR: {e}")


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




def load_tts():
    global tts_pipeline
    try:
        _log("[tts] *** load_tts thread started ***")
        _log(f"[tts] APP_DIR={APP_DIR}")

        py311_paths = [
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\python.exe"),
            r"C:\Users\bubag\AppData\Local\Programs\Python\Python311\python.exe",
        ]
        py311 = None
        for p in py311_paths:
            _log(f"[tts] checking: {p} exists={os.path.exists(p)}")
            if os.path.exists(p):
                py311 = p
                break

        if not py311:
            import subprocess
            result = subprocess.run(["where", "python"], capture_output=True, text=True)
            for line in result.stdout.strip().splitlines():
                if "311" in line and os.path.exists(line.strip()):
                    py311 = line.strip()
                    break

        if not py311:
            _log("[tts] ERROR: Python 3.11 not found")
            return

        _log(f"[tts] Python 3.11 found: {py311}")
        # Set immediately — don't test (test blocks startup for 30+ seconds)
        tts_pipeline = py311
        _log("[tts] TTS ready — will use Kokoro via Python 3.11 subprocess")

    except Exception as e:
        import traceback
        _log(f"[tts] FATAL: {e}")
        _log(traceback.format_exc())


def run_http_server(cfg):
    from http.server import HTTPServer, BaseHTTPRequestHandler

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

            # Config endpoint — returns current model to the HTML
            if path == "config":
                body = json.dumps({
                    "model": cfg.get("model", "llama3"),
                    "ollama_host": OLLAMA_HOST,
                }).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.send_cors()
                self.end_headers()
                self.wfile.write(body)
                return

            if path == "":
                path = "ollama-voice-chat.html"
            file_path = APP_DIR / path
            if not file_path.exists() or not file_path.is_file():
                self.send_response(404); self.end_headers()
                self.wfile.write(b"Not found"); return

            ext  = file_path.suffix.lower()
            mime = {".html":"text/html",".js":"application/javascript",
                    ".css":"text/css",".png":"image/png",".ico":"image/x-icon"
                    }.get(ext, "application/octet-stream")
            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.send_cors(); self.end_headers()
            self.wfile.write(data)

        def do_POST(self):
            # /speak — Kokoro TTS
            if self.path == "/speak":
                try:
                    import tempfile as _tf, os, subprocess, json as _json
                    cl = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(cl)
                    req_data = _json.loads(body)
                    text  = req_data.get("text", "").strip()[:800]
                    speed = float(req_data.get("speed", 0.9))
                    speed = max(0.2, min(5.0, speed))  # clamp to valid range
                    _log(f"[tts] /speak called, text length={len(text)}, speed={speed}")
                    if not text:
                        self._json_error("No text"); return

                    # Find Python 3.11
                    py311 = None
                    for p in [
                        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Python\Python311\python.exe"),
                        r"C:\Users\bubag\AppData\Local\Programs\Python\Python311\python.exe",
                    ]:
                        if os.path.exists(p):
                            py311 = p
                            break
                    _log(f"[tts] py311={py311}")
                    if not py311:
                        self._json_error("Python 3.11 not found"); return

                    # Write text to temp file
                    txt = _tf.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8")
                    txt.write(text); txt.close()
                    wav = _tf.NamedTemporaryFile(suffix=".wav", delete=False)
                    wav.close()
                    _log(f"[tts] tmp files: txt={txt.name} wav={wav.name}")

                    script = "\n".join([
                        "import sys",
                        "from kokoro import KPipeline",
                        "import numpy as np, soundfile as sf",
                        f"with open(r'{txt.name}', encoding='utf-8') as f: text=f.read()",
                        "p = KPipeline(lang_code='b')",
                        "s = []",
                        f"[s.append(a) for _,_,a in p(text, voice='bm_george', speed={speed})]",
                        "if not s: print('NO_AUDIO'); sys.exit(1)",
                        f"sf.write(r'{wav.name}', np.concatenate(s), 24000)",
                        "print('WAV_OK')",
                    ])

                    result = subprocess.run(
                        [py311, "-c", script],
                        capture_output=True, text=True, timeout=120
                    )
                    _log(f"[tts] subprocess exit={result.returncode}")
                    _log(f"[tts] stdout={result.stdout[-300:].strip()}")
                    if result.stderr: _log(f"[tts] stderr={result.stderr[-300:].strip()}")

                    try: os.unlink(txt.name)
                    except: pass

                    if "WAV_OK" not in result.stdout:
                        self._json_error(f"TTS failed: {result.stderr[-200:]}"); return

                    with open(wav.name, "rb") as f:
                        wav_bytes = f.read()
                    try: os.unlink(wav.name)
                    except: pass

                    self.send_response(200)
                    self.send_header("Content-Type", "audio/wav")
                    self.send_header("Content-Length", str(len(wav_bytes)))
                    self.send_cors(); self.end_headers()
                    self.wfile.write(wav_bytes)
                    _log(f"[tts] Spoke {len(text)} chars OK")
                except Exception as e:
                    import traceback
                    _log(f"[tts] /speak EXCEPTION: {e}")
                    _log(traceback.format_exc())
                    self._json_error(str(e))
                return

            if self.path != "/transcribe":
                self.send_response(404); self.end_headers(); return
            if whisper_model is None:
                self._json_error("Whisper model not loaded yet"); return

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
                print(f"[whisper] Transcript: {transcript!r}")
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

    global http_server
    http_server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[server] Listening on http://localhost:{PORT}")
    http_server.serve_forever()


# ================================================================
#  SYSTEM TRAY
# ================================================================

def create_tray(cfg):
    try:
        import pystray
        from PIL import Image, ImageDraw

        img  = Image.new("RGB", (64,64), color=(12,12,14))
        draw = ImageDraw.Draw(img)
        s = 1.0
        draw.ellipse([0,0,63,63], fill=(30,30,30))
        draw.rounded_rectangle([16,18,48,50], radius=8, fill=(232,255,71))
        draw.ellipse([14,10,26,26], fill=(232,255,71))
        draw.ellipse([38,10,50,26], fill=(232,255,71))
        draw.ellipse([17,13,23,22], fill=(30,30,30))
        draw.ellipse([41,13,47,22], fill=(30,30,30))
        draw.ellipse([21,26,25,30], fill=(30,30,30))
        draw.ellipse([39,26,43,30], fill=(30,30,30))
        draw.ellipse([26,44,30,48], fill=(30,30,30))
        draw.ellipse([34,44,38,48], fill=(30,30,30))

        model_label = cfg.get("model","llama3")

        def on_open(icon, item):
            webbrowser.open(f"http://localhost:{PORT}/ollama-voice-chat.html")

        def on_quit(icon, item):
            print("[tray] Quitting...")
            icon.stop()
            if http_server: http_server.shutdown()
            docker(["stop","ollama"])
            os._exit(0)

        menu = pystray.Menu(
            pystray.MenuItem(f"Model: {model_label}", None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Voice UI", on_open, default=True),
            pystray.MenuItem("Quit", on_quit),
        )
        icon = pystray.Icon("OllamaVoice", img, "OllamaVoice", menu)
        print("[tray] System tray icon active")
        icon.run()

    except ImportError:
        print("[tray] pystray not available — close this window to quit.")
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            docker(["stop","ollama"])
            sys.exit(0)


# ================================================================
#  MAIN
# ================================================================

if __name__ == "__main__":
    print("=" * 52)
    print("  OLLAMAVOICE — Local AI Voice Assistant")
    print("=" * 52)
    _log(f"[startup] OllamaVoice starting. Log: {_LOG_FILE}")
    _log(f"[startup] APP_DIR={APP_DIR}")

    # 1. Load config
    cfg = load_config()

    # 2. Ensure Docker Desktop is running
    ensure_docker()

    # 3. Ensure Ollama container exists and is started
    ensure_ollama_container()

    # 4. Show model selector dialog
    print("[ui] Opening model selector...")
    selected = show_model_selector(cfg.get("model", "llama3"))
    cfg["model"] = selected
    save_config(cfg)
    print(f"[ui] Selected model: {selected}")

    # 5. Start HTTP server + Whisper in background
    threading.Thread(target=run_http_server, args=(cfg,), daemon=True).start()
    threading.Thread(target=load_whisper, daemon=True).start()

    # 6. Launch selected LLM in background
    threading.Thread(target=launch_model, args=(selected,), daemon=True).start()

    # 7. Open browser
    time.sleep(3)
    print(f"[browser] Opening http://localhost:{PORT}/ollama-voice-chat.html")
    webbrowser.open(f"http://localhost:{PORT}/ollama-voice-chat.html")

    # 8. System tray (blocks main thread)
    create_tray(cfg)
