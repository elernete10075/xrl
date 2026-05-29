Invoke-WebRequest -Uri "https://raw.githubusercontent.com/elernete10075/xrl/main/serviceAccountKey.json" -OutFile "serviceAccountKey.json"


# Установка XRL-CHAT для Windows
$targetDir = "$env:USERPROFILE\xrl-chat"
$launcherName = "launcher_win.py"

# Создаем папку
if (!(Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir | Out-Null }

Write-Host "Downloading Windows Launcher..." -ForegroundColor Cyan
$url = "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/$launcherName"
Invoke-WebRequest -Uri $url -OutFile "$targetDir\$launcherName"

# Создаем команду для запуска
$batPath = "$env:USERPROFILE\start-xrl.bat"
$batContent = "@echo off`ncd /d `"$targetDir`"`npython $launcherName"
[System.IO.File]::WriteAllText($batPath, $batContent)

Write-Host "Success! Installation complete." -ForegroundColor Green
Write-Host "To start, type: start-xrl" -ForegroundColor Yellow
