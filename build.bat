@echo off
cd /d "%~dp0"

echo [1/3] Building ZapretGUI.exe ...
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto err
python -m PyInstaller --noconfirm --onefile --windowed --uac-admin --icon icon.ico --add-data "icon.ico;." --name ZapretGUI main.py
if errorlevel 1 goto err
if not exist "dist\ZapretGUI.exe" goto err

echo [2/3] Building installer ...
set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=%LocalAppData%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" goto noinno
"%ISCC%" installer.iss
if errorlevel 1 goto err

echo [3/3] Making zip ...
powershell -NoProfile -Command "Compress-Archive -Force -Path 'installer\ZapretGUI-Setup.exe' -DestinationPath 'installer\ZapretGUI-Setup.zip'"
if errorlevel 1 goto err

echo.
echo DONE: installer\ZapretGUI-Setup.zip
pause
exit /b 0

:noinno
echo.
echo Inno Setup 6 not found. Install it with:  winget install JRSoftware.InnoSetup
echo Then run build.bat again. (dist\ZapretGUI.exe is already built.)
pause
exit /b 1

:err
echo.
echo BUILD FAILED. See messages above.
pause
exit /b 1
