#define MyAppName "FINDUS>x<STRETCHING"
#define MyAppExeName "findus_stretching.exe"
#define MyAppPublisher "FindusXstreck"
#ifndef MyAppVersion
  #define MyAppVersion "0.1.9"
#endif
#define MyAppURL "https://example.invalid/findusxstreck"

[Setup]
AppId={{7D40B376-1312-4ADB-BBE1-85F79F4A31E4}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\FindusXstreck
DefaultGroupName=FindusXstreck
DisableProgramGroupPage=yes
LicenseFile=
PrivilegesRequired=lowest
OutputDir=dist\installer
OutputBaseFilename=findus_stretching_setup_v{#MyAppVersion}
SetupIconFile=assets\findus_stretching_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\findus_stretching\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
