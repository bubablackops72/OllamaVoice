================================================================
  OllamaVoice - Local AI Voice Assistant
  README & Complete Guide
  Version 1.2
================================================================

OllamaVoice is a fully local, private AI voice assistant that
runs entirely on your own PC. Your voice, your data, your hardware.
No cloud. No subscriptions. No internet required after first setup.

================================================================
  WHAT'S NEW IN VERSION 1.2
================================================================

  - Jarvis voice (Kokoro TTS) now working via Python 3.11 subprocess
  - Speed control: 0.2x to 5.0x in the header, saved between sessions
  - Stop button: instantly stops Jarvis mid-sentence
  - JARVIS ON/OFF toggle button in the header
  - Config and setup data moved to AppData (no permissions issues)
  - Install path corrected to 64-bit Program Files
  - Build cache auto-cleared on every create_installer.bat run
  - Auto-copies updated exe to install dir after each build

================================================================
  WHAT'S IN VERSION 1.1
================================================================

  - Model selector dialog on every launch
  - Support for 5 AI models: Llama 3, Mistral 22B, Qwen 2.5 32B,
    DeepSeek R1 32B, Gemma 2 27B
  - Docker Desktop auto-starts if not running
  - 100% GPU mode for all model inference
  - All CPU cores for fast model loading
  - Startup screen with 6 live status checks before mic unlocks
  - LLM warmup step before mic activates
  - Local Whisper transcription (faster-whisper) — fully offline
  - CPU-throttled model downloads (12.5% via .wslconfig)
  - Single PowerShell progress window per model download
  - Windows installer with model selection checkboxes
  - System tray icon showing active model name

================================================================
  SUPPORTED AI MODELS
================================================================

  Model              Size     Best for
  ─────────────────────────────────────────────────────────────
  Llama 3            ~4.7 GB  Fast, general purpose (default)
  Mistral 22B        ~13 GB   Balanced performance
  Qwen 2.5 32B       ~19 GB   Excellent reasoning
  DeepSeek R1 32B    ~19 GB   Coding and complex reasoning
  Gemma 2 27B        ~16 GB   Google open model

  NOTE: DeepSeek R1 uses a "thinking" architecture — it generates
  an internal chain of thought before answering. Expect 30-60
  seconds before the first token appears. This is normal.

  RECOMMENDED: RTX 5090 (32GB VRAM) runs any model up to 32B
  at 100% GPU with no CPU offload.

================================================================
  REQUIREMENTS
================================================================

  - Windows 10 or 11 (64-bit)
  - Docker Desktop  https://www.docker.com/products/docker-desktop/
    Launch and wait for "Engine running" before use
  - Python 3.11     https://www.python.org/downloads/
    CHECK "Add Python to PATH" during install
    (Python 3.11 specifically required for Kokoro TTS voice)
  - NVIDIA GPU recommended for best performance

================================================================
  INSTALLATION
================================================================

  STEP 1 - Install Docker Desktop and Python 3.11
    Make sure Docker Desktop shows "Engine running" before
    continuing. Python 3.11 is required for Jarvis voice.

  STEP 2 - Run the installer
    Double-click: OllamaVoice_Setup.exe
    Run as administrator if prompted.

    The installer will:
      - Install Python 3.11 silently if not found
      - Install Python packages (Kokoro TTS, faster-whisper, etc.)
      - Create and start the Ollama Docker container
      - Show model selection checkboxes
      - Download selected models one at a time with progress window
      - Optionally create a Desktop shortcut
      - Optionally launch on Windows startup

  STEP 3 - Model downloads
    Each selected model opens a PowerShell progress window:
      - CPU limited to 12.5% via .wslconfig (PC stays usable)
      - Progress bar shows size, speed, and ETA
      - Verification step confirms each model installed correctly
      - Window closes automatically, next model begins
      - Full CPU restored when all downloads complete

================================================================
  FIRST LAUNCH
================================================================

  1. Docker Desktop auto-starts if not running

  2. Model selector dialog — choose your AI model for this session
     Your choice is saved. The tray icon shows the active model.

  3. Startup screen — 6 status checks:
     o Config loaded
     o Ollama connected
     o Whisper server ready
     o Jarvis voice (Kokoro TTS) loading
     o Model found
     o LLM warming up
     Everything stays locked until all pass green.

  4. Browser opens automatically when ready

================================================================
  USING OLLAMAVOICE
================================================================

  VOICE INPUT
    Click the mic button (bottom left)
    Speak your message
    Click mic again to stop
    Speech transcribed locally via Whisper → sent to LLM

  TEXT INPUT
    Type in the text box → press Enter or click SEND

  JARVIS VOICE OUTPUT
    Every LLM response is read aloud by Kokoro TTS (bm_george)
    Deep British male voice — closest local match to Jarvis

  SPEED CONTROL  (top right, next to JARVIS ON/OFF)
    Range: 0.2x (very slow) to 5.0x (very fast)
    Increments: 0.2x up to 2.0x, then 2.5x, 3.0x, 4.0x, 5.0x
    Setting is saved between sessions

  STOP BUTTON  (appears while Jarvis is speaking)
    Click [|| STOP] to instantly silence Jarvis mid-sentence
    Clears the entire speech queue

  JARVIS ON/OFF TOGGLE
    Click the JARVIS ON/OFF button to toggle voice on or off
    Does not stop current speech — use STOP for that

  SWITCHING MODELS
    Quit from the tray icon and relaunch
    The model selector appears on every launch

  SYSTEM TRAY ICON  (bottom right taskbar)
    Right-click to:
      Open Voice UI  — reopens the browser
      Quit           — shuts everything down cleanly

================================================================
  PERFORMANCE NOTES
================================================================

  GPU USAGE
    OllamaVoice forces 100% GPU inference:
      OLLAMA_NUM_GPU=999          all layers on GPU
      OLLAMA_GPU_LAYERS=999       all transformer layers on GPU
      OLLAMA_MAIN_GPU=0           targets GPU 0 explicitly
      OLLAMA_FLASH_ATTENTION=1    reduces VRAM usage
      OLLAMA_KV_CACHE_TYPE=q8_0   halves KV cache VRAM footprint

    Verify GPU usage:
      docker --context default exec ollama ollama ps

  JARVIS VOICE (KOKORO TTS)
    First speech call: ~10-30 seconds (model loads into memory)
    Subsequent calls: ~2-5 seconds depending on text length
    Kokoro model cached at:
      C:\Users\<you>\.cache\huggingface\hub\models--hexgrad--Kokoro-82M\
    Runs entirely offline after first load

  WHISPER
    Speech recognition: faster-whisper "base" model (~150MB)
    Fully offline, runs on CPU, ~1-3 seconds per recording

================================================================
  TROUBLESHOOTING
================================================================

  "Ollama unreachable"
    Open Docker Desktop, wait for "Engine running", relaunch.

  "Whisper server not running"
    Quit from tray and relaunch.

  Jarvis voice not working / JARVIS OFF shown
    Check that Python 3.11 is installed:
      C:\Users\<you>\AppData\Local\Programs\Python\Python311\python.exe
    Check debug log at: %TEMP%\ollamavoice_debug.log

  First Jarvis response is slow (~30 seconds)
    Normal — Kokoro loads its model on first use then caches it.
    Subsequent responses are much faster.

  "Model not found"
    Open [ config ] and confirm Chat Model name matches exactly.
    Check installed models:
      docker --context default exec ollama ollama list

  "Microphone access denied"
    Click lock icon in browser address bar → Set Microphone to Allow

  Model shows CPU% instead of 100% GPU
    Delete %APPDATA%\OllamaVoice\.ollama_setup_done
    Relaunch to recreate container with GPU settings.

  Docker won't stop
    Force stop:  docker --context default kill ollama
    Nuclear:     wsl --shutdown

  Browser doesn't open
    Navigate to: http://localhost:8080/ollama-voice-chat.html

================================================================
  FILE LOCATIONS
================================================================

  Install directory (read-only, exe and static files):
    C:\Program Files\OllamaVoice\

  Config and setup flags (writable):
    C:\Users\<you>\AppData\Roaming\OllamaVoice\config.json

  Debug log:
    C:\Users\<you>\AppData\Local\Temp\ollamavoice_debug.log

  Kokoro voice model cache:
    C:\Users\<you>\.cache\huggingface\hub\

  Whisper model cache:
    C:\Users\<you>\.cache\huggingface\hub\

================================================================
  USEFUL COMMANDS
================================================================

  List installed models:
    docker --context default exec ollama ollama list

  Check running model and GPU usage:
    docker --context default exec ollama ollama ps

  Remove a model:
    docker --context default exec ollama ollama rm <modelname>

  Pull a model manually:
    docker --context default exec ollama ollama pull <modelname>

  Live container stats:
    docker --context default stats ollama

  Force stop container:
    docker --context default kill ollama

  Full WSL2 shutdown:
    wsl --shutdown

================================================================
  UNINSTALLING
================================================================

  Settings > Apps > OllamaVoice > Uninstall

  Removes: app files, shortcuts, Start Menu, startup entry
  Does NOT remove: Docker, Python, Ollama, AI models, packages

  To also remove Kokoro voice cache:
    Delete: C:\Users\<you>\.cache\huggingface\hub\

================================================================
  FOR DEVELOPERS - BUILDING THE INSTALLER
================================================================

  SOURCE FILES (all in same folder):
    launcher.py             main app entry point
    ollama_server.py        fallback Whisper + HTTP server
    ollama-voice-chat.html  browser UI
    OllamaVoice.iss         Inno Setup installer script
    create_installer.bat    builds OllamaVoice_Setup.exe
    create_icon.py          generates Ollama-style .ico
    pull_model.ps1          per-model download with CPU throttle
    README.txt              this file

  BUILD STEPS:
    1. Extract source zip to a fresh folder
    2. Run create_installer.bat as a NORMAL USER (not admin)
       PyInstaller does not work correctly as admin
    3. It automatically:
         - Installs/verifies Python 3.11
         - Installs kokoro, faster-whisper, pystray, pyinstaller into 3.11
         - Clears old build cache (forces full recompile every time)
         - Generates ollama_icon.ico
         - Compiles OllamaVoice.exe with Python 3.11
         - Downloads Inno Setup if not installed
         - Compiles OllamaVoice_Setup.exe
         - Copies updated files to existing install if present
    4. Run OllamaVoice_Setup.exe as admin to install

  KEY ARCHITECTURE NOTES:
    - Kokoro TTS runs via Python 3.11 subprocess (NOT bundled in exe)
      This avoids PyInstaller frozen environment incompatibilities
    - config.json lives in %APPDATA%\OllamaVoice\ (writable)
    - Static files (HTML, server, scripts) live in Program Files (read-only)
    - Speed setting persisted in browser localStorage
    - All TTS events logged to %TEMP%\ollamavoice_debug.log

================================================================
  PRIVACY & SECURITY
================================================================

  Everything runs locally:
    Voice transcription  faster-whisper on CPU
    AI inference         Ollama in Docker on GPU
    TTS voice            Kokoro on Python 3.11
    Web UI               Python HTTP server (localhost only)

  No data sent externally. No account or API key needed.
  No internet after initial model and voice model downloads.

================================================================
  Version    : 1.2
  Platform   : Windows 10/11 (64-bit)
  Powered by : Python 3.11, Kokoro TTS, faster-whisper, Ollama, Docker
  Voice      : Kokoro bm_george (British male)
  Models     : Llama 3, Mistral 22B, Qwen 2.5 32B,
               DeepSeek R1 32B, Gemma 2 27B
================================================================
