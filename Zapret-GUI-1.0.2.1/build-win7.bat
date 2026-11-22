@echo off
cd /d "%~dp0"
echo Build for Windows 7: needs Python 3.8 x64 (python.org, version 3.8.10).
py -3.8 --version
if errorlevel 1 goto nopy

echo [1/2] Creating environment ...
py -3.8 -m venv .venv-win7
if errorlevel 1 goto err
".venv-win7\Scripts\python.exe" -m pip install --upgrade pip
".venv-win7\Scripts\python.exe" -m pip install -r requirements-win7.txt pyinstaller==5.13.2
if errorlevel 1 goto err

echo [2/2] Building ZapretGUI-Win7.exe ...
".venv-win7\Scripts\python.exe" -m PyInstaller --noconfirm --onefile --windowed --uac-admin --icon icon.ico --add-data "icon.ico;." --name ZapretGUI-Win7 main.py
if errorlevel 1 goto err
if not exist "dist\ZapretGUI-Win7.exe" goto err

echo.
echo DONE: dist\ZapretGUI-Win7.exe
pause
exit /b 0

:nopy
echo.
echo Python 3.8 not found. Install it from https://www.python.org/downloads/release/python-3810/
pause
exit /b 1

:err
echo.
echo BUILD FAILED. See messages above.
pause
exit /b 1
