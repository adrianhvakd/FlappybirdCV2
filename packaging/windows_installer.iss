#define AppName "Flappy Bird Visión"
#define AppVersion "1.0.0"
#define AppPublisher "Flappy Bird Visión"
#define AppExe "FlappyBirdVision.exe"
#define DistDir "..\dist\FlappyBirdVision"

[Setup]
AppId={{8F2A1C34-9B7E-4E2A-9C1D-0A1B2C3D4E5F}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\FlappyBirdVision
UninstallDisplayName={#AppName}
DefaultGroupName={#AppName}
OutputDir=..\dist
OutputBaseFilename=FlappyBirdVision-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"; Flags: unchecked

[Files]
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "Ejecutar {#AppName}"; Flags: nowait postinstall skipifsilent
