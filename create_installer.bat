@echo off
title OllamaVoice - Build Windows Installer
setlocal

set SCRIPT_DIR=%~dp0
set INNO_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
set INNO_EXE2=C:\Program Files\Inno Setup 6\ISCC.exe
set INNO_URL=https://github.com/jrsoftware/issrc/releases/download/is-6_3_3/innosetup-6.3.3.exe
set INNO_INSTALLER=%TEMP%\innosetup-6.3.3.exe

:: Python 3.11 paths (preferred for TTS compatibility)
set PY311=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
set PY311_PIP=%LOCALAPPDATA%\Programs\Python\Python311\Scripts\pip.exe
set PY311_PYINSTALLER=%LOCALAPPDATA%\Programs\Python\Python311\Scripts\pyinstaller.exe

:: Python 3.11 installer URL
set PY311_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe
set PY311_INSTALLER=%TEMP%\python-3.11.9-amd64.exe

echo ================================================================
echo  OllamaVoice - Windows Installer Builder
echo  Using Python 3.11 for Kokoro TTS compatibility
echo ================================================================
echo.

echo [1/7] Checking Python 3.11...
if exist "%PY311%" (
    echo  [OK] Python 3.11 found at %PY311%
    goto HAVE_PY311
)

echo  Python 3.11 not found. Downloading (~27MB)...
powershell -Command "Invoke-WebRequest -Uri '%PY311_URL%' -OutFile '%PY311_INSTALLER%' -UseBasicParsing"
if errorlevel 1 (
    echo  ERROR: Failed to download Python 3.11
    pause & exit /b 1
)

echo  Installing Python 3.11 (alongside your existing Python)...
"%PY311_INSTALLER%" /quiet InstallAllUsers=0 PrependPath=0 Include_test=0
if errorlevel 1 (
    echo  ERROR: Python 3.11 install failed
    pause & exit /b 1
)

if not exist "%PY311%" (
    echo  ERROR: Python 3.11 not found after install at expected path.
    echo  Expected: %PY311%
    pause & exit /b 1
)
echo  [OK] Python 3.11 installed.

:HAVE_PY311

echo.
echo [2/7] Checking source files...
set MISSING=0
if not exist "%SCRIPT_DIR%launcher.py"            ( echo  [!] Missing: launcher.py            & set MISSING=1 )
if not exist "%SCRIPT_DIR%ollama_server.py"       ( echo  [!] Missing: ollama_server.py       & set MISSING=1 )
if not exist "%SCRIPT_DIR%ollama-voice-chat.html" ( echo  [!] Missing: ollama-voice-chat.html & set MISSING=1 )
if not exist "%SCRIPT_DIR%OllamaVoice.iss"        ( echo  [!] Missing: OllamaVoice.iss        & set MISSING=1 )
if not exist "%SCRIPT_DIR%create_icon.py"         ( echo  [!] Missing: create_icon.py         & set MISSING=1 )
if not exist "%SCRIPT_DIR%pull_model.ps1"         ( echo  [!] Missing: pull_model.ps1         & set MISSING=1 )
if "%MISSING%"=="1" (
    echo  ERROR: Missing files. All files must be in the same folder.
    pause & exit /b 1
)
echo  [OK] All source files found.

echo.
echo [3/7] Installing Python packages into Python 3.11...
"%PY311%" -m pip install --upgrade pip --quiet 2>nul
"%PY311%" -m pip install pillow pyinstaller faster-whisper pystray kokoro soundfile numpy --quiet
if errorlevel 1 (
    echo  WARNING: Some packages may not have installed correctly.
)
echo  [OK] Python 3.11 packages ready.

echo.
echo [4/7] Generating Ollama-style icon...
cd /d "%SCRIPT_DIR%"
"%PY311%" create_icon.py
if errorlevel 1 ( echo  ERROR: Icon generation failed. & pause & exit /b 1 )
if not exist "%SCRIPT_DIR%ollama_icon.ico" ( echo  ERROR: Icon not created. & pause & exit /b 1 )
echo  [OK] Icon created.

echo.
echo [5/7] Cleaning build cache and recompiling from scratch...
if exist "%SCRIPT_DIR%build" rmdir /s /q "%SCRIPT_DIR%build"
if exist "%SCRIPT_DIR%dist"  rmdir /s /q "%SCRIPT_DIR%dist"
if exist "%SCRIPT_DIR%OllamaVoice.exe"   del /f /q "%SCRIPT_DIR%OllamaVoice.exe"
if exist "%SCRIPT_DIR%OllamaVoice.spec"  del /f /q "%SCRIPT_DIR%OllamaVoice.spec"
echo  [OK] Build cache cleared - forcing full recompile.
echo.
echo [5/7] Compiling OllamaVoice.exe with Python 3.11...
cd /d "%SCRIPT_DIR%"

"%PY311_PYINSTALLER%" ^
    --onefile ^
    --console ^
    --name "OllamaVoice" ^
    --icon "ollama_icon.ico" ^
    --add-data "ollama-voice-chat.html;." ^
    --add-data "ollama_server.py;." ^
    --add-data "pull_model.ps1;." ^
    --hidden-import faster_whisper ^
    --hidden-import pystray ^
    --hidden-import PIL ^
    --hidden-import PIL.Image ^
    --hidden-import PIL.ImageDraw ^
    --hidden-import kokoro ^
    --hidden-import soundfile ^
    launcher.py

if not exist "%SCRIPT_DIR%dist\OllamaVoice.exe" (
    echo  ERROR: OllamaVoice.exe not created.
    pause & exit /b 1
)
copy "%SCRIPT_DIR%dist\OllamaVoice.exe" "%SCRIPT_DIR%OllamaVoice.exe" >nul
echo  [OK] OllamaVoice.exe compiled with Python 3.11 + Kokoro TTS.

echo.
echo [6/7] Installing runtime packages for end users (Python 3.11)...
echo  (These will be used by OllamaVoice at runtime)
echo  Note: Kokoro model (~500MB) downloads on first voice use.

echo.
echo [7/7] Building Windows installer with Inno Setup...

if exist "%INNO_EXE%" goto COMPILE
if exist "%INNO_EXE2%" ( set INNO_EXE=%INNO_EXE2% & goto COMPILE )

echo  Downloading Inno Setup...
powershell -Command "Invoke-WebRequest -Uri '%INNO_URL%' -OutFile '%INNO_INSTALLER%' -UseBasicParsing"
if errorlevel 1 ( echo  ERROR: Download failed. & pause & exit /b 1 )
"%INNO_INSTALLER%" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
timeout /t 8 /nobreak >nul

if exist "%INNO_EXE%" goto COMPILE
if exist "%INNO_EXE2%" ( set INNO_EXE=%INNO_EXE2% & goto COMPILE )
echo  ERROR: Inno Setup not found after install.
pause & exit /b 1

:COMPILE
"%INNO_EXE%" OllamaVoice.iss
if errorlevel 1 ( echo  ERROR: Compilation failed. & pause & exit /b 1 )

echo.
echo ================================================================
echo  SUCCESS! OllamaVoice_Setup.exe is ready.
echo  Built with Python 3.11 + Kokoro TTS (Jarvis voice: bm_george)
echo ================================================================
echo.
echo ================================================================
echo  Auto-updating installed version...
echo ================================================================

:: Stop any running OllamaVoice instances
taskkill /f /im OllamaVoice.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: Copy new exe directly to install dir if it exists
set INSTALL_DIR=
if exist "C:\Program Files\OllamaVoice\OllamaVoice.exe"       set INSTALL_DIR=C:\Program Files\OllamaVoice
if exist "C:\Program Files (x86)\OllamaVoice\OllamaVoice.exe" set INSTALL_DIR=C:\Program Files (x86)\OllamaVoice

if defined INSTALL_DIR (
    echo  Copying new files to %INSTALL_DIR%...
    copy /y "%SCRIPT_DIR%OllamaVoice.exe"          "%INSTALL_DIR%\OllamaVoice.exe" >nul
    copy /y "%SCRIPT_DIR%ollama-voice-chat.html"   "%INSTALL_DIR%\ollama-voice-chat.html" >nul
    copy /y "%SCRIPT_DIR%ollama_server.py"          "%INSTALL_DIR%\ollama_server.py" >nul
    echo  [OK] Updated: %INSTALL_DIR%
) else (
    echo  No existing install found - run OllamaVoice_Setup.exe to install.
)

echo.
set /p OPEN=  Open folder? (Y/N): 
if /i "%OPEN%"=="Y" explorer "%SCRIPT_DIR%"
pause