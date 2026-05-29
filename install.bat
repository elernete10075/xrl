@echo off
echo Starting XRL-CHAT installation...
echo ______________________________________

set TARGET_DIR=%USERPROFILE%\xrl-chat
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

echo Downloading launcher...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/launcher.py' -OutFile '%TARGET_DIR%\launcher.py'"

echo Setting up launch command...
set LAUNCHER_BAT=%USERPROFILE%\start-xrl.bat
echo @echo off > "%LAUNCHER_BAT%"
echo cd /d "%TARGET_DIR%" >> "%LAUNCHER_BAT%"
echo python launcher.py >> "%LAUNCHER_BAT%"

echo Installation finished!
pause
