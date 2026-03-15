@echo off
title OllamaVoice - Build Windows Installer
setlocal

set SCRIPT_DIR=%~dp0
set INNO_URL=https://github.com/jrsoftware/issrc/releases/download/is-6_3_3/innosetup-6.3.3.exe
set INNO_INSTALLER=%TEMP%\innosetup-6.3.3.exe
set INNO_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
set INNO_EXE2=C:\Program Files\Inno Setup 6\ISCC.exe
set PYINSTALLER_PATH=%LOCALAPPDATA%\Python\pythoncore-3.14-64\Scripts\pyinstaller.exe

echo ================================================================
echo  OllamaVoice - Windows Installer Builder
echo ================================================================
echo.

:: ── Step 1: Python check ─────────────────────────────────────────
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo  ERROR: Python not found. Install from https://www.python.org/downloads/
  pause & exit /b 1
)
echo  [OK] Python found.

:: ── Step 2: Check source files ───────────────────────────────────
echo.
echo [2/6] Checking source files...
set MISSING=0
if not exist "%SCRIPT_DIR%launcher.py"            ( echo  [!] Missing: launcher.py            & set MISSING=1 )
if not exist "%SCRIPT_DIR%ollama_server.py"       ( echo  [!] Missing: ollama_server.py       & set MISSING=1 )
if not exist "%SCRIPT_DIR%ollama-voice-chat.html" ( echo  [!] Missing: ollama-voice-chat.html & set MISSING=1 )
if not exist "%SCRIPT_DIR%OllamaVoice.iss"        ( echo  [!] Missing: OllamaVoice.iss        & set MISSING=1 )
if not exist "%SCRIPT_DIR%create_icon.py"         ( echo  [!] Missing: create_icon.py         & set MISSING=1 )
if "%MISSING%"=="1" (
  echo  ERROR: Missing required files. Make sure all files are in the same folder.
  pause & exit /b 1
)
echo  [OK] All source files found.

:: ── Step 3: Install Python packages ─────────────────────────────
echo.
echo [3/6] Installing Python packages...
pip install pillow pyinstaller faster-whisper pystray --quiet
echo  [OK] Packages ready.

:: ── Step 4: Generate icon ────────────────────────────────────────
echo.
echo [4/6] Generating Ollama-style icon...
cd /d "%SCRIPT_DIR%"
python create_icon.py
if errorlevel 1 (
  echo  ERROR: Icon generation failed.
  pause & exit /b 1
)
if not exist "%SCRIPT_DIR%ollama_icon.ico" (
  echo  ERROR: ollama_icon.ico was not created.
  pause & exit /b 1
)
echo  [OK] Icon created: ollama_icon.ico

:: ── Step 5: Compile OllamaVoice.exe with PyInstaller ────────────
echo.
echo [5/6] Compiling OllamaVoice.exe (this takes 2-3 minutes)...
cd /d "%SCRIPT_DIR%"

:: Try pyinstaller on PATH first, then fall back to known location
pyinstaller --version >nul 2>&1
if not errorlevel 1 (
  pyinstaller ^
    --onefile ^
    --console ^
    --name "OllamaVoice" ^
    --icon "ollama_icon.ico" ^
    --add-data "ollama-voice-chat.html;." ^
    --add-data "ollama_server.py;." ^
    --hidden-import faster_whisper ^
    --hidden-import pystray ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageDraw ^
    launcher.py
  goto CHECK_EXE
)

if exist "%PYINSTALLER_PATH%" (
  "%PYINSTALLER_PATH%" ^
    --onefile ^
    --console ^
    --name "OllamaVoice" ^
    --icon "ollama_icon.ico" ^
    --add-data "ollama-voice-chat.html;." ^
    --add-data "ollama_server.py;." ^
    --hidden-import faster_whisper ^
    --hidden-import pystray ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageDraw ^
    launcher.py
  goto CHECK_EXE
)

:: Last resort - find pyinstaller anywhere in AppData
for /f "delims=" %%i in ('where /r "%LOCALAPPDATA%" pyinstaller.exe 2^>nul') do (
  "%%i" ^
    --onefile ^
    --console ^
    --name "OllamaVoice" ^
    --icon "ollama_icon.ico" ^
    --add-data "ollama-voice-chat.html;." ^
    --add-data "ollama_server.py;." ^
    --hidden-import faster_whisper ^
    --hidden-import pystray ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageDraw ^
    launcher.py
  goto CHECK_EXE
)

echo  ERROR: pyinstaller.exe not found. Try closing and reopening this window.
pause & exit /b 1

:CHECK_EXE
if not exist "%SCRIPT_DIR%dist\OllamaVoice.exe" (
  echo  ERROR: OllamaVoice.exe was not created. Check PyInstaller output above.
  pause & exit /b 1
)

:: Move exe to script dir for Inno Setup
copy "%SCRIPT_DIR%dist\OllamaVoice.exe" "%SCRIPT_DIR%OllamaVoice.exe" >nul
echo  [OK] OllamaVoice.exe compiled with custom icon.

:: ── Step 6: Build installer ──────────────────────────────────────
echo.
echo [6/6] Building Windows installer with Inno Setup...

if exist "%INNO_EXE%" goto COMPILE
if exist "%INNO_EXE2%" ( set INNO_EXE=%INNO_EXE2% & goto COMPILE )

echo  Downloading Inno Setup (~10MB)...
powershell -Command "Invoke-WebRequest -Uri '%INNO_URL%' -OutFile '%INNO_INSTALLER%' -UseBasicParsing"
if errorlevel 1 (
  echo  ERROR: Download failed.
  echo  Install Inno Setup manually from: https://jrsoftware.org/isdl.php
  pause & exit /b 1
)
echo  Installing Inno Setup silently...
"%INNO_INSTALLER%" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
timeout /t 8 /nobreak >nul

if exist "%INNO_EXE%" goto COMPILE
if exist "%INNO_EXE2%" ( set INNO_EXE=%INNO_EXE2% & goto COMPILE )
echo  ERROR: Inno Setup not found after install.
echo  Install manually from: https://jrsoftware.org/isdl.php
pause & exit /b 1

:COMPILE
echo  Compiling installer...
"%INNO_EXE%" OllamaVoice.iss
if errorlevel 1 (
  echo  ERROR: Inno Setup compilation failed.
  pause & exit /b 1
)

echo.
echo ================================================================
echo  SUCCESS!
echo.
echo  OllamaVoice_Setup.exe has been created in:
echo  %SCRIPT_DIR%
echo.
echo  Share OllamaVoice_Setup.exe with anyone.
echo  They double-click it to install like any Windows app.
echo  The installer includes the custom llama icon on all shortcuts.
echo ================================================================
echo.
set /p OPEN=  Open folder? (Y/N): 
if /i "%OPEN%"=="Y" explorer "%SCRIPT_DIR%"
pause
