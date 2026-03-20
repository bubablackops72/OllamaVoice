@echo off
title OllamaVoice - Build Windows Installer
setlocal

set SCRIPT_DIR=%~dp0
set INNO_URL=https://github.com/jrsoftware/issrc/releases/download/is-6_3_3/innosetup-6.3.3.exe
set INNO_INSTALLER=%TEMP%\innosetup-6.3.3.exe
set INNO_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
set INNO_EXE2=C:\Program Files\Inno Setup 6\ISCC.exe

echo ================================================================
echo  OllamaVoice - Windows Installer Builder
echo ================================================================
echo.

echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
  echo  ERROR: Python not found.
  pause & exit /b 1
)
echo  [OK] Python found.

echo.
echo [2/6] Checking source files...
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
echo [3/6] Installing Python packages...
pip install pillow pyinstaller faster-whisper pystray --quiet
echo  [OK] Packages ready.

echo.
echo [4/6] Generating Ollama-style icon...
cd /d "%SCRIPT_DIR%"
python create_icon.py
if errorlevel 1 ( echo  ERROR: Icon generation failed. & pause & exit /b 1 )
if not exist "%SCRIPT_DIR%ollama_icon.ico" ( echo  ERROR: Icon not created. & pause & exit /b 1 )
echo  [OK] Icon created.

echo.
echo [5/6] Compiling OllamaVoice.exe...
cd /d "%SCRIPT_DIR%"

pyinstaller --version >nul 2>&1
if not errorlevel 1 goto RUN_PYINSTALLER

for /f "delims=" %%i in ('where /r "%LOCALAPPDATA%" pyinstaller.exe 2^>nul') do (
  set PYINSTALLER_PATH=%%i
  goto RUN_PYINSTALLER
)
echo  ERROR: pyinstaller not found. Close and reopen this window after pip install.
pause & exit /b 1

:RUN_PYINSTALLER
if defined PYINSTALLER_PATH (
  "%PYINSTALLER_PATH%" --onefile --console --name "OllamaVoice" --icon "ollama_icon.ico" --add-data "ollama-voice-chat.html;." --add-data "ollama_server.py;." --add-data "pull_model.ps1;." --hidden-import faster_whisper --hidden-import pystray --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageDraw launcher.py
) else (
  pyinstaller --onefile --console --name "OllamaVoice" --icon "ollama_icon.ico" --add-data "ollama-voice-chat.html;." --add-data "ollama_server.py;." --add-data "pull_model.ps1;." --hidden-import faster_whisper --hidden-import pystray --hidden-import PIL --hidden-import PIL.Image --hidden-import PIL.ImageDraw launcher.py
)

if not exist "%SCRIPT_DIR%dist\OllamaVoice.exe" (
  echo  ERROR: OllamaVoice.exe not created.
  pause & exit /b 1
)
copy "%SCRIPT_DIR%dist\OllamaVoice.exe" "%SCRIPT_DIR%OllamaVoice.exe" >nul
echo  [OK] OllamaVoice.exe compiled with custom icon.

echo.
echo [6/6] Building Windows installer with Inno Setup...

if exist "%INNO_EXE%" goto COMPILE
if exist "%INNO_EXE2%" ( set INNO_EXE=%INNO_EXE2% & goto COMPILE )

echo  Downloading Inno Setup (~10MB)...
powershell -Command "Invoke-WebRequest -Uri '%INNO_URL%' -OutFile '%INNO_INSTALLER%' -UseBasicParsing"
if errorlevel 1 (
  echo  ERROR: Download failed. Install from: https://jrsoftware.org/isdl.php
  pause & exit /b 1
)
echo  Installing Inno Setup...
"%INNO_INSTALLER%" /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
timeout /t 8 /nobreak >nul

if exist "%INNO_EXE%" goto COMPILE
if exist "%INNO_EXE2%" ( set INNO_EXE=%INNO_EXE2% & goto COMPILE )
echo  ERROR: Inno Setup not found. Install from: https://jrsoftware.org/isdl.php
pause & exit /b 1

:COMPILE
"%INNO_EXE%" OllamaVoice.iss
if errorlevel 1 ( echo  ERROR: Compilation failed. & pause & exit /b 1 )

echo.
echo ================================================================
echo  SUCCESS! OllamaVoice_Setup.exe is ready in:
echo  %SCRIPT_DIR%
echo.
echo  The installer includes:
echo    - Custom llama icon on all shortcuts
echo    - Model selection checkboxes (Llama3, Mistral 22B,
echo      Qwen 2.5 32B, DeepSeek R1 32B, Gemma 2 27B)
echo    - Desktop shortcut option
echo    - Windows Startup option
echo    - Automatic model downloads during install
echo ================================================================
echo.
set /p OPEN=  Open folder? (Y/N): 
if /i "%OPEN%"=="Y" explorer "%SCRIPT_DIR%"
pause
