@echo off
chcp 65001 >nul
echo Установка XRL-CHAT Bootstrapper для Windows...
echo ______________________________________
echo.

set TARGET_DIR=%USERPROFILE%\xrl-chat
if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

echo [1/3] Скачивание launcher.py...
powershell -Command "Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/launcher.py' -OutFile '%TARGET_DIR%\launcher.py'"

echo [2/3] Настройка команды запуска...
set LAUNCHER_BAT=%USERPROFILE%\start-xrl.bat
echo @echo off > "%LAUNCHER_BAT%"
echo cd /d "%TARGET_DIR%" >> "%LAUNCHER_BAT%"
echo python launcher.py >> "%LAUNCHER_BAT%"

echo [3/3] Установка завершена!
pause
