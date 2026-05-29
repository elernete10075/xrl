# Установка XRL-CHAT
$ErrorActionPreference = 'Stop'
$targetDir = "$env:USERPROFILE\xrl-chat"

# Создаем папку, если ее нет
if (!(Test-Path $targetDir)) { New-Item -ItemType Directory -Path $targetDir | Out-Null }

Write-Host "Downloading XRL-CHAT..." -ForegroundColor Cyan
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/launcher.py" -OutFile "$targetDir\launcher.py"

# Создаем файл для быстрого запуска (аналог start-xrl)
$batPath = "$env:USERPROFILE\start-xrl.bat"
$batContent = "@echo off`ncd /d `"$targetDir`"`npython launcher.py"
[System.IO.File]::WriteAllText($batPath, $batContent)

Write-Host "Success! Installation complete." -ForegroundColor Green
Write-Host "To start, type: start-xrl" -ForegroundColor Yellow
