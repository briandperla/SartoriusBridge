; Inno Setup Script for SartoriusBridge Windows Installer
; Requires Inno Setup 6.0+ (https://jrsoftware.org/isinfo.php)

#define MyAppName "Sartorius Bridge"
#define MyAppVersion "1.4.1"
#define MyAppPublisher "Focal Finishes"
#define MyAppURL "https://github.com/brianperla/SartoriusBridge"
#define MyAppExeName "SartoriusBridge.exe"

[Setup]
; App identification
AppId={{B8F3E4A2-5C1D-4E8F-9A2B-6D7C8E9F0A1B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}/releases

; Install location
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output settings
OutputDir=..\dist
OutputBaseFilename=SartoriusBridge-Setup-{#MyAppVersion}
SetupIconFile=..\assets\SartoriusBridge.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression
Compression=lzma2
SolidCompression=yes

; Privileges (no admin required - installs to user folder by default)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Windows version requirement
MinVersion=10.0

; Visual settings
WizardStyle=modern
WizardSizePercent=100

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start automatically with Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
; Main executable (built by PyInstaller)
Source: "..\dist\SartoriusBridge.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

; Desktop (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Startup (optional)
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startupicon

[Run]
; Option to run after install
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Stop the app before uninstalling
Filename: "taskkill"; Parameters: "/F /IM {#MyAppExeName}"; Flags: runhidden; RunOnceId: "StopApp"

[Code]
// Check if app is running before uninstall
function InitializeUninstall(): Boolean;
var
  ResultCode: Integer;
begin
  // Try to stop the app gracefully
  Exec('taskkill', '/F /IM SartoriusBridge.exe', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := True;
end;
