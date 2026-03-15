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

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &Desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked
Name: "startupicon"; Description: "Launch OllamaVoice automatically when &Windows starts"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "OllamaVoice.exe";         DestDir: "{app}"; Flags: ignoreversion
Source: "ollama_server.py";        DestDir: "{app}"; Flags: ignoreversion
Source: "ollama-voice-chat.html";  DestDir: "{app}"; Flags: ignoreversion
Source: "ollama_icon.ico";         DestDir: "{app}"; Flags: ignoreversion
Source: "README.txt";              DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{group}\OllamaVoice";           Filename: "{app}\OllamaVoice.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ollama_icon.ico"; Comment: "Ollama Voice Assistant"
Name: "{group}\Uninstall OllamaVoice"; Filename: "{uninstallexe}"
Name: "{autodesktop}\OllamaVoice";     Filename: "{app}\OllamaVoice.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ollama_icon.ico"; Comment: "Ollama Voice Assistant"; Tasks: desktopicon
Name: "{userstartup}\OllamaVoice";     Filename: "{app}\OllamaVoice.exe"; WorkingDir: "{app}"; IconFilename: "{app}\ollama_icon.ico"; Tasks: startupicon

[Run]
Filename: "pip"; Parameters: "install faster-whisper pystray pillow --quiet"; StatusMsg: "Installing Python packages..."; Flags: runhidden waituntilterminated
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
    if MsgBox('Docker Desktop does not appear to be installed or running.' + #13#10 + #13#10 +
              'OllamaVoice requires Docker Desktop to run the AI model.' + #13#10 +
              'Download: https://www.docker.com/products/docker-desktop/' + #13#10 + #13#10 +
              'Continue anyway and install Docker before first launch?',
              mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False; Exit;
    end;
  end;
  if not Exec('cmd.exe', '/c python --version >nul 2>&1', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) or (ResultCode <> 0) then
  begin
    if MsgBox('Python does not appear to be installed.' + #13#10 + #13#10 +
              'OllamaVoice requires Python 3.10 or higher.' + #13#10 +
              'Download: https://www.python.org/downloads/' + #13#10 +
              'Check "Add Python to PATH" during install.' + #13#10 + #13#10 +
              'Continue anyway and install Python before first launch?',
              mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False; Exit;
    end;
  end;
end;
