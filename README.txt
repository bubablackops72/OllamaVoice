================================================================
  OllamaVoice - Local AI Voice Assistant
  README & Complete Guide
  Version 1.1
================================================================

OllamaVoice is a fully local, private AI voice assistant that
runs entirely on your own PC. Your voice, your data, your hardware.
No cloud. No subscriptions. No internet required after first setup.

================================================================
  WHAT'S NEW IN VERSION 1.1
================================================================

  - Model selector dialog on every launch — choose your AI model
    before the session starts
  - Support for 5 AI models: Llama 3, Mistral 22B, Qwen 2.5 32B,
    DeepSeek R1 32B, Gemma 2 27B
  - Docker Desktop auto-starts if not already running
  - 100% GPU mode — all model layers forced onto GPU, no CPU offload
    using OLLAMA_MAIN_GPU, OLLAMA_KV_CACHE_TYPE=q8_0, and
    OLLAMA_FLASH_ATTENTION for maximum speed
  - All CPU cores available at runtime for fast model loading
  - Startup screen with 5 live status checks before mic unlocks
  - LLM warmup step — mic stays locked until model is fully ready
  - Local Whisper transcription (faster-whisper) — fully offline
  - CPU-throttled model downloads during install (12.5% CPU cap
    via .wslconfig) to prevent overheating
  - Single PowerShell progress window per model download with
    verification step after each download
  - Windows installer (Inno Setup) with model selection checkboxes,
    desktop shortcut option, and startup option
  - System tray icon showing active model name
  - Config endpoint — browser reads selected model from server

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

  NOTE: DeepSeek R1 uses a "thinking" architecture. It generates
  an internal reasoning chain before answering — expect 30-60
  seconds before the first token appears. This is normal.

  RECOMMENDED: RTX 5090 (32GB VRAM) can run any model up to
  32B at full GPU with no CPU offload.

================================================================
  REQUIREMENTS
================================================================

  - Windows 10 or 11
  - Docker Desktop  https://www.docker.com/products/docker-desktop/
    Launch and wait for "Engine running" before use
  - Python 3.10+    https://www.python.org/downloads/
    CHECK "Add Python to PATH" during install
  - NVIDIA GPU recommended for best performance

================================================================
  INSTALLATION
================================================================

  STEP 1 - Install Docker Desktop and Python (if not installed)
    Make sure Docker Desktop is running before continuing.

  STEP 2 - Run the installer
    Double-click: OllamaVoice_Setup.exe
    Run as administrator if prompted.

    The installer will:
      - Check Docker and Python are installed
      - Install Python packages (faster-whisper, pystray, pillow)
      - Create and start the Ollama Docker container
      - Show model selection checkboxes
      - Download selected models one at a time
      - Ask if you want a Desktop shortcut (optional)
      - Ask if you want OllamaVoice on Windows startup (optional)
      - Offer to launch immediately when done

  STEP 3 - Model downloads
    Each model opens a PowerShell progress window showing:
      - Download progress with size, speed and ETA
      - CPU limited to 12.5% to prevent overheating
      - Verification confirms model installed correctly
      - Window closes automatically, next model starts
      - Full CPU restored after all downloads complete

================================================================
  FIRST LAUNCH
================================================================

  1. Docker Desktop auto-starts if not already running
     OllamaVoice launches Docker Desktop automatically and waits
     up to 60 seconds for it to be ready.

  2. Model selector dialog appears
     Choose which installed model to use for this session.
     Your choice is saved. The tray icon shows the active model.

  3. Browser startup screen shows 5 status checks:
     o Connecting to Ollama
     o Connecting to Whisper transcription server
     o Checking selected model is installed
     o Warming up LLM (waits until model is fully loaded)
     o Requesting microphone access
     Everything stays locked until all 5 pass green.

  4. Browser opens automatically when ready.

================================================================
  USING OLLAMAVOICE
================================================================

  VOICE INPUT
    Click the mic button (bottom left)
    Speak your message
    Click mic again to stop
    Speech is transcribed locally then sent to the LLM

  TEXT INPUT
    Type in the text box and press Enter or click SEND

  SYSTEM TRAY ICON
    Right-click the tray icon (bottom right taskbar) to:
      Open Voice UI  — reopens the browser
      Quit           — shuts everything down cleanly

  SWITCHING MODELS
    Quit from the tray icon and relaunch.
    The model selector appears on every launch.

  CONFIG PANEL
    Click [ config ] in the browser top-right to change:
      Ollama Host, Chat Model, Transcription URL

================================================================
  PERFORMANCE NOTES
================================================================

  GPU USAGE
    OllamaVoice forces 100% GPU inference using:
      OLLAMA_NUM_GPU=999          all layers on GPU
      OLLAMA_GPU_LAYERS=999       all transformer layers on GPU
      OLLAMA_MAIN_GPU=0           targets GPU 0 explicitly
      OLLAMA_FLASH_ATTENTION=1    reduces VRAM usage
      OLLAMA_KV_CACHE_TYPE=q8_0   halves KV cache VRAM footprint

    Verify 100% GPU is being used:
      docker --context default exec ollama ollama ps

  CPU USAGE
    Model downloads (install only) : 12.5% CPU cap
    Whisper transcription          : all CPU cores
    LLM model loading              : all CPU cores
    LLM token generation           : GPU handles this

================================================================
  TROUBLESHOOTING
================================================================

  "Ollama unreachable"
    Open Docker Desktop, wait for "Engine running", relaunch.

  "Whisper server not running"
    Quit from tray and relaunch. Check Python is on PATH.

  "Model not found"
    Open [ config ] and confirm Chat Model name is correct.
    Check installed models:
      docker --context default exec ollama ollama list

  "Microphone access denied"
    Click the lock icon in your browser address bar.
    Set Microphone to Allow. Refresh the page (F5).

  Model shows CPU% instead of 100% GPU
    Delete .ollama_setup_done from C:\Program Files\OllamaVoice\
    Relaunch to recreate container with GPU settings.
    Large context windows consume VRAM for KV cache which can
    push layers to CPU if VRAM is full.

  Docker won't stop
    Force stop:  docker --context default kill ollama
    Nuclear:     wsl --shutdown  (stops all WSL2 instantly)

  Browser doesn't open
    Navigate manually: http://localhost:8080/ollama-voice-chat.html

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

  Option 1: Settings > Apps > OllamaVoice > Uninstall
  Option 2: Start > OllamaVoice > Uninstall OllamaVoice

  Removes: app files, shortcuts, Start Menu, startup entry
  Does NOT remove: Docker, Python, Ollama, AI models, packages

================================================================
  FOR DEVELOPERS - BUILDING THE INSTALLER
================================================================

  SOURCE FILES (all must be in same folder):
    launcher.py             main app entry point
    ollama_server.py        local Whisper + HTTP server
    ollama-voice-chat.html  browser UI
    OllamaVoice.iss         Inno Setup installer script
    create_installer.bat    builds OllamaVoice_Setup.exe
    create_icon.py          generates Ollama-style .ico
    pull_model.ps1          per-model download with CPU throttle
    README.txt              this file

  BUILD STEPS:
    1. Extract source zip anywhere on your PC
    2. Right-click create_installer.bat > Run as administrator
    3. It automatically:
         - Installs pyinstaller, pillow, faster-whisper, pystray
         - Generates ollama_icon.ico
         - Compiles launcher.py into OllamaVoice.exe
         - Downloads Inno Setup if needed
         - Compiles OllamaVoice_Setup.exe
    4. Share OllamaVoice_Setup.exe — users only need this file

  ARCHITECTURE OVERVIEW:
    launcher.py
      Detects/starts Docker Desktop
      Creates Ollama container with 100% GPU env vars
      Shows tkinter model selector dialog
      Saves model choice to config.json
      Starts HTTP server (/transcribe, /config, static files)
      Loads faster-whisper with all CPU cores
      Launches selected model with all CPU cores + 100% GPU
      Opens browser, runs system tray icon

    pull_model.ps1 (installer only)
      Backs up .wslconfig
      Writes CPU-limited .wslconfig (processors=N at 12.5%)
      Restarts WSL2 to apply limit
      Runs ollama pull directly (native progress bar)
      Verifies install via ollama list
      Restores .wslconfig, restarts WSL2 to full CPU
      Exits so installer moves to next model

================================================================
  PRIVACY & SECURITY
================================================================

  Everything runs locally:
    Voice transcription  faster-whisper on CPU (local)
    AI inference         Ollama in Docker (local GPU)
    Web UI               Python HTTP server (localhost only)

  No data sent externally. No account or API key needed.
  No internet after initial model downloads.
  Google Fonts loaded for UI typography only (cosmetic).

================================================================
  Version    : 1.1
  Platform   : Windows 10/11
  Powered by : Python, faster-whisper, Ollama, Docker
  Models     : Llama 3, Mistral 22B, Qwen 2.5 32B,
               DeepSeek R1 32B, Gemma 2 27B
================================================================
