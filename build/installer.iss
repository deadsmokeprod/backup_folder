; Inno Setup скрипт для BackupBots
; Сборка: iscc build/installer.iss

#define MyAppName "BackupBots"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "deadsmokeprod"
#define MyAppURL "https://github.com/deadsmokeprod/backup_folder"
#define MyAppGuiExe "BackupApp.exe"
#define MyAppServiceExe "BackupService.exe"

[Setup]
AppId={{8F9B9A1E-BA33-4F7C-8F86-BACKUPBOTS001}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\dist\installer
OutputBaseFilename=BackupBotsSetup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
UninstallDisplayIcon={app}\BackupApp\{#MyAppGuiExe}
SetupIconFile=
DisableWelcomePage=no
DisableReadyPage=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Дополнительные значки:"; Flags: checkedonce

[Files]
Source: "..\dist\BackupApp\*"; DestDir: "{app}\BackupApp"; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\dist\BackupService\*"; DestDir: "{app}\BackupService"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\BackupApp\{#MyAppGuiExe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\BackupApp\{#MyAppGuiExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\BackupService\{#MyAppServiceExe}"; Parameters: "--startup auto install"; Flags: runhidden waituntilterminated; StatusMsg: "Регистрирую службу резервного копирования..."
Filename: "{app}\BackupService\{#MyAppServiceExe}"; Parameters: "start"; Flags: runhidden waituntilterminated; StatusMsg: "Запускаю службу..."
Filename: "{app}\BackupApp\{#MyAppGuiExe}"; Description: "Открыть BackupBots сейчас"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\BackupService\{#MyAppServiceExe}"; Parameters: "stop"; Flags: runhidden waituntilterminated; RunOnceId: "StopService"
Filename: "{app}\BackupService\{#MyAppServiceExe}"; Parameters: "remove"; Flags: runhidden waituntilterminated; RunOnceId: "RemoveService"
