; OllamaVoice Inno Setup Script

#define AppName "OllamaVoice"
#define AppVersion "1.0"
#define AppPublisher "OllamaVoice"
#define AppExeName "OllamaVoice.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\OllamaVoice
DefaultGroupName={#AppName}
AllowNoIcons=yes
OutputDir=.
OutputBaseFilename=OllamaVoice_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
SetupIconFile=ollama_icon.ico
UninstallDisplayName=OllamaVoice
UninstallDisplayIcon={app}\OllamaVoice.exe
ExtraDiskSpaceRequired=75161927680

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";       Description: "Create a &Desktop shortcut";                          GroupDescription: "Shortcuts:"; Flags: unchecked
Name: "startupicon";       Description: "Launch OllamaVoice automatically when Windows starts"; GroupDescription: "Shortcuts:"; Flags: unchecked
Name: "model_llama3";      Description: "Llama 3         (~4.7 GB)  - Fast, efficient";         GroupDescription: "AI Models to install (select at least one):"; Flags: checkedonce
Name: "model_mistral22b";  Description: "Mistral 22B     (~13 GB)   - Balanced performance";    GroupDescription: "AI Models to install (select at least one):"; Flags: unchecked
Name: "model_qwen32b";     Description: "Qwen 2.5 32B    (~19 GB)   - Excellent reasoning";     GroupDescription: "AI Models to install (select at least one):"; Flags: unchecked
Name: "model_deepseek32b"; Description: "DeepSeek R1 32B (~19 GB)   - Best coding & reasoning"; GroupDescription: "AI Models to install (select at least one):"; Flags: unchecked
Name: "model_gemma27b";    Description: "Gemma 2 27B     (~16 GB)   - Google open model";       GroupDescription: "AI Models to install (select at least one):"; Flags: unchecked

[Files]
Source: "OllamaVoice.exe";         DestDir: "{app}"; Flags: ignoreversion
Source: "ollama_server.py";        DestDir: "{app}"; Flags: ignoreversion
Source: "ollama-voice-chat.html";  DestDir: "{app}"; Flags: ignoreversion
Source: "ollama_icon.ico";         DestDir: "{app}"; Flags: ignoreversion
Source: "pull_model.ps1";          DestDir: "{app}"; Flags: ignoreversion
Source: "README.txt";              DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\OllamaVoice";           Filename: "{app}\OllamaVoice.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ollama_icon.ico"; Comment: "Ollama Voice Assistant"
Name: "{group}\Uninstall OllamaVoice"; Filename: "{uninstallexe}"
Name: "{autodesktop}\OllamaVoice";     Filename: "{app}\OllamaVoice.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ollama_icon.ico"; Tasks: desktopicon
Name: "{userstartup}\OllamaVoice";     Filename: "{app}\OllamaVoice.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ollama_icon.ico"; Tasks: startupicon

[Run]
; Step 1 - Python packages
Filename: "pip"; Parameters: "install faster-whisper pystray pillow --quiet"; StatusMsg: "Installing Python packages..."; Flags: runhidden waituntilterminated

; Step 2 - Start or create Ollama container
Filename: "cmd.exe"; Parameters: "/c docker --context default start ollama 2>nul || docker --context default run -d --gpus all --name ollama -p 11434:11434 -e OLLAMA_ORIGINS=* -e OLLAMA_KEEP_ALIVE=-1 -v ollama:/root/.ollama ollama/ollama"; StatusMsg: "Starting Ollama container..."; Flags: runhidden waituntilterminated
Filename: "cmd.exe"; Parameters: "/c timeout /t 10 /nobreak"; StatusMsg: "Waiting for Ollama to initialize..."; Flags: runhidden waituntilterminated

; Step 3 - Download each selected model one at a time
; Each opens its own window, downloads, verifies, restores CPU, then closes
; The installer waits for each to finish before starting the next
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\pull_model.ps1"" -Model ""llama3""";            StatusMsg: "Downloading Llama 3 - see progress window..."; Flags: waituntilterminated; Tasks: model_llama3
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\pull_model.ps1"" -Model ""mistral-small:22b"""; StatusMsg: "Downloading Mistral 22B - see progress window..."; Flags: waituntilterminated; Tasks: model_mistral22b
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\pull_model.ps1"" -Model ""qwen2.5:32b""";       StatusMsg: "Downloading Qwen 2.5 32B - see progress window..."; Flags: waituntilterminated; Tasks: model_qwen32b
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\pull_model.ps1"" -Model ""deepseek-r1:32b""";   StatusMsg: "Downloading DeepSeek R1 32B - see progress window..."; Flags: waituntilterminated; Tasks: model_deepseek32b
Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -File ""{app}\pull_model.ps1"" -Model ""gemma2:27b""";        StatusMsg: "Downloading Gemma 2 27B - see progress window..."; Flags: waituntilterminated; Tasks: model_gemma27b

; Step 4 - Write setup flag
Filename: "cmd.exe"; Parameters: "/c echo done > ""{app}\.ollama_setup_done"""; Flags: runhidden waituntilterminated

; Step 5 - Launch
Filename: "{app}\OllamaVoice.exe"; Description: "Launch OllamaVoice now"; Flags: nowait postinstall skipifsilent shellexec

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if not Exec('cmd.exe', '/c docker --version >nul 2>&1', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
  begin
    if MsgBox(
      'Docker Desktop is not installed or not running.' + #13#10 + #13#10 +
      'OllamaVoice requires Docker Desktop.' + #13#10 +
      'Download: https://www.docker.com/products/docker-desktop/' + #13#10 + #13#10 +
      'Make sure Docker Desktop shows "Engine running" before continuing.' + #13#10 + #13#10 +
      'Continue anyway?',
      mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False; Exit;
    end;
  end;
  if not Exec('cmd.exe', '/c python --version >nul 2>&1', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
  begin
    if MsgBox(
      'Python is not installed.' + #13#10 + #13#10 +
      'OllamaVoice requires Python 3.10+.' + #13#10 +
      'Download: https://www.python.org/downloads/' + #13#10 +
      'IMPORTANT: Check "Add Python to PATH" during install.' + #13#10 + #13#10 +
      'Continue anyway?',
      mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False; Exit;
    end;
  end;
end;
