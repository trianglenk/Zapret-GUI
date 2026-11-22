; Установщик Zapret GUI (Inno Setup 6)
; Ставится как обычное приложение: папка C:\Program Files\Zapret GUI (можно сменить в мастере),
; ярлыки в меню «Пуск» и на рабочем столе, запись в «Установленных приложениях».
; В одной папке: ZapretGUI.exe + release + backup + downloads + config.json
#ifndef AppVer
  #define AppVer "1.0.2.2"
#endif
#ifndef ExeSrc
  #define ExeSrc "dist\ZapretGUI.exe"
#endif
#ifndef OutName
  #define OutName "ZapretGUI-Setup"
#endif

[Setup]
AppName=Zapret GUI
AppVersion={#AppVer}
AppPublisher=Zapret GUI
AppId={{7D3F6A52-91B4-4C1E-8A27-5E0B9C4D1F63}
DefaultDirName={autopf}\Zapret GUI
UsePreviousAppDir=yes
DefaultGroupName=Zapret GUI
DisableProgramGroupPage=yes
DisableDirPage=no
OutputDir=installer
OutputBaseFilename={#OutName}
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\ZapretGUI.exe
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
CloseApplications=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать ярлык на рабочем столе"; GroupDescription: "Ярлыки:"
Name: "autostart"; Description: "Запускать вместе с Windows (в трее)"; GroupDescription: "Дополнительно:"; Flags: unchecked

[Dirs]
Name: "{app}\release"
Name: "{app}\backup"
Name: "{app}\downloads"
Name: "{app}\profiles"

[Files]
Source: "{#ExeSrc}"; DestDir: "{app}"; DestName: "ZapretGUI.exe"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\Zapret GUI"; Filename: "{app}\ZapretGUI.exe"
Name: "{autodesktop}\Zapret GUI"; Filename: "{app}\ZapretGUI.exe"; Tasks: desktopicon

[Run]
Filename: "schtasks"; Parameters: "/create /tn ZapretGUI /tr ""\""{app}\ZapretGUI.exe\"" --minimized"" /sc onlogon /rl highest /f"; Flags: runhidden; Tasks: autostart
Filename: "{app}\ZapretGUI.exe"; Description: "Запустить Zapret GUI"; Flags: nowait postinstall skipifsilent runascurrentuser; WorkingDir: "{app}"

[UninstallRun]
Filename: "taskkill"; Parameters: "/IM ZapretGUI.exe /F"; Flags: runhidden; RunOnceId: "KillApp"
Filename: "taskkill"; Parameters: "/IM winws.exe /F"; Flags: runhidden; RunOnceId: "KillWinws"
Filename: "schtasks"; Parameters: "/delete /tn ZapretGUI /f"; Flags: runhidden; RunOnceId: "DelTask"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\release"
Type: filesandordirs; Name: "{app}\backup"
Type: filesandordirs; Name: "{app}\downloads"
Type: filesandordirs; Name: "{app}\profiles"
Type: files; Name: "{app}\config.json"
Type: files; Name: "{app}\winws.log"
