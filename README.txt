================================================================
  OllamaVoice - Local AI Voice Assistant
  README & Complete Guide
================================================================

OllamaVoice is a fully local, private AI voice assistant that
runs entirely on your own PC. Your voice, your data, your hardware.
No cloud. No subscriptions. No internet required after first setup.

================================================================
  FOR END USERS - INSTALLING OLLAMAVOICE
================================================================

  STEP 1 - Install Requirements
  --------------------------------
  Before running the installer, you need:

  A) DOCKER DESKTOP
     Download: https://www.docker.com/products/docker-desktop/
     - Run the installer
     - Launch Docker Desktop after install
     - Wait until the bottom-left shows "Engine running"
     - Keep Docker Desktop running whenever you use OllamaVoice

  B) PYTHON 3.10 OR HIGHER
     Download: https://www.python.org/downloads/
     - Run the installer
     - !! CHECK "Add Python to PATH" on the first screen !!
     - OR install from Microsoft Store (search "Python 3")

  STEP 2 - Run the Installer
  --------------------------------
  Double-click:  OllamaVoice_Setup.exe

  The installer will:
    - Check that Docker and Python are installed
    - Show a warning if anything is missing (you can still proceed
      and install the missing items before first launch)
    - Let you choose an install directory (default is fine)
    - Ask if you want a Desktop shortcut
    - Ask if you want OllamaVoice to launch on Windows startup
    - Install Python packages automatically (faster-whisper, etc.)
    - Offer to launch OllamaVoice immediately when done

  STEP 3 - First Launch
  --------------------------------
  The very first time OllamaVoice launches:

    1. It pulls the Ollama Docker image (~1GB)
       Only happens once. Skipped if Ollama is already installed.

    2. It downloads the Whisper speech model (~150MB)
       Only happens once. Saved permanently to your PC.

    3. It loads the llama3 AI model into GPU memory
       Takes 30-60 seconds. Faster on subsequent launches.

  You will see a startup screen with 5 status checks:
    o Connecting to Ollama
    o Connecting to Whisper transcription server
    o Checking llama3 model
    o Warming up LLM (waits until the model is fully ready)
    o Requesting microphone access

  Everything is locked until all 5 checks pass green.
  Your browser opens automatically when the system is ready.

================================================================
  USING OLLAMAVOICE
================================================================

  VOICE INPUT
    Click the microphone button (bottom left circle)
    Speak your message clearly
    Click the microphone button again to stop recording
    Your speech is transcribed locally and sent to the AI

  TEXT INPUT
    Type in the text box at the bottom of the screen
    Press Enter or click SEND

  SYSTEM TRAY ICON
    OllamaVoice shows an icon in your taskbar (bottom right)
    Right-click it to:
      Open Voice UI  - reopens the browser window
      Quit           - shuts down everything cleanly

  CONFIG PANEL
    Click [ config ] in the top-right of the browser to change:
      Ollama Host       - default: http://localhost:11434
      Chat Model        - default: llama3
      Transcription URL - default: http://localhost:8080/transcribe

================================================================
  TROUBLESHOOTING
================================================================

  "Ollama unreachable" on startup screen
    - Open Docker Desktop and wait for "Engine running"
    - Restart Docker Desktop if it looks stuck
    - Try relaunching OllamaVoice after Docker is ready

  "Whisper server not running"
    - Close OllamaVoice completely (tray icon > Quit)
    - Relaunch OllamaVoice_Setup.exe or the Desktop shortcut
    - Make sure Python is installed and on PATH:
        Open PowerShell and type: python --version

  "Model not found"
    - Click [ config ] in the browser
    - Make sure Chat Model is set to: llama3
    - The model name must exactly match what Ollama has installed

  "Microphone access denied"
    - Click the lock/settings icon in your browser address bar
    - Set Microphone permission to Allow
    - Refresh the page (F5)

  "Generating..." with no response / stuck
    - The LLM may still be loading into GPU memory
    - The startup screen now waits for the LLM before unlocking
    - If stuck more than 3 minutes, close and relaunch

  Browser window doesn't open
    - Open your browser manually and go to:
        http://localhost:8080/ollama-voice-chat.html

  App won't start / crashes immediately
    - Make sure Docker Desktop is running first
    - Make sure Python is installed:
        Open PowerShell, type: python --version
    - Make sure packages are installed:
        Open PowerShell, type: pip show faster-whisper

================================================================
  UNINSTALLING
================================================================

  Option 1: Windows Settings
    Settings > Apps > OllamaVoice > Uninstall

  Option 2: Start Menu
    Start > OllamaVoice > Uninstall OllamaVoice

  The uninstaller removes:
    - All installed app files
    - Desktop shortcut (if created)
    - Start Menu entries
    - Startup entry (if added)

  The uninstaller does NOT remove:
    - Docker Desktop
    - Python
    - Ollama Docker image
    - Any downloaded AI models (llama3, Whisper)
    - Python packages (faster-whisper, pystray, pillow)

================================================================
  FOR DEVELOPERS - BUILDING THE INSTALLER
================================================================

  To build OllamaVoice_Setup.exe from source:

  REQUIREMENTS:
    - Windows 10 or 11
    - Python 3.10+ with pip on PATH
    - Internet connection (to download Inno Setup ~5MB)
    - All source files in the same folder:
        launcher.py
        ollama_server.py
        ollama-voice-chat.html
        OllamaVoice.iss
        run.bat
        uninstall_helper.bat
        create_installer.bat
        README.txt

  STEPS:
    1. Extract this zip anywhere on your PC
    2. Double-click create_installer.bat
    3. It will:
         - Download and install Inno Setup automatically
         - Install required Python packages
         - Compile everything into OllamaVoice_Setup.exe
    4. Share OllamaVoice_Setup.exe with anyone
       (they only need the single .exe file)

  NOTE: create_installer.bat can be run from any folder.
  No need to copy anything to your Desktop.

================================================================
  PRIVACY & SECURITY
================================================================

  Everything runs locally on your PC:
    - Voice transcription: OpenAI Whisper (Python, CPU)
    - AI model: llama3 via Ollama (Docker container)
    - Web UI: Python HTTP server (localhost only)

  No data is sent to any external server.
  No account or API key required.
  No internet needed after the initial model downloads.

  The only external resource used is Google Fonts in the browser
  UI (cosmetic fonts only - the app works without them).

================================================================
  Version: 1.0
  Powered by: Python, faster-whisper, Ollama, Docker, llama3
================================================================
