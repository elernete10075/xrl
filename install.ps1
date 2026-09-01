# ==========================================
#  XRL-CHAT INSTALLER FOR WINDOWS
# ==========================================

Clear-Host

# Вывод логотипа ECHO при запуске
Write-Host "        ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  " -ForegroundColor Cyan
Write-Host "        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ " -ForegroundColor Cyan
Write-Host "        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ " -ForegroundColor Magenta
Write-Host "        ░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░ " -ForegroundColor Magenta
Write-Host "        ░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ " -ForegroundColor DarkMagenta
Write-Host "        ░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ " -ForegroundColor DarkMagenta
Write-Host "        ░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  " -ForegroundColor DarkMagenta
Write-Host "`n========================================================" -ForegroundColor Gray
Write-Host "             INSTALLING XRL-CHAT SYSTEM                " -ForegroundColor Yellow
Write-Host "========================================================`n" -ForegroundColor Gray

# Настройки путей
$targetDir = "$env:USERPROFILE\xrl-chat"
$launcherName = "launcher_win.py"
$keyName = "Server_1.json"

# Создаем рабочую директорию
if (!(Test-Path $targetDir)) { 
    New-Item -ItemType Directory -Path $targetDir | Out-Null 
}

# 1. Скачивание конфига Firebase (Server_1.json)
Write-Host "[1/3] Downloading Server_1.json configuration..." -ForegroundColor Cyan
$keyUrl = "https://raw.githubusercontent.com/elernete10075/xrl/main/$keyName"
try {
    Invoke-WebRequest -Uri $keyUrl -OutFile "$targetDir\$keyName"
    Write-Host "     -> Server_1.json saved successfully." -ForegroundColor Gray
} catch {
    Write-Host "     [ERROR] Failed to download $keyName!" -ForegroundColor Red
}

# 2. Скачивание лаунчера
Write-Host "[2/3] Downloading Windows Launcher..." -ForegroundColor Cyan
$launcherUrl = "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/$launcherName"
try {
    Invoke-WebRequest -Uri $launcherUrl -OutFile "$targetDir\$launcherName"
    Write-Host "     -> $launcherName saved successfully." -ForegroundColor Gray
} catch {
    Write-Host "     [ERROR] Failed to download $launcherName!" -ForegroundColor Red
}

# 3. Создание ярлыка быстрого запуска в командной строке
Write-Host "[3/3] Creating start-xrl command..." -ForegroundColor Cyan
$batPath = "$env:USERPROFILE\start-xrl.bat"
$batContent = "@echo off`ncd /d `"$targetDir`"`npython $launcherName"
[System.IO.File]::WriteAllText($batPath, $batContent)

Write-Host "`n--------------------------------------------------------" -ForegroundColor Gray
Write-Host " SUCCESS! Installation complete." -ForegroundColor Green
Write-Host " To start the application, type: start-xrl" -ForegroundColor Yellow
Write-Host "--------------------------------------------------------`n" -ForegroundColor Gray
