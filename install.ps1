Clear-Host

Write-Host "░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  " -ForegroundColor Cyan
Write-Host "░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ " -ForegroundColor Cyan
Write-Host "░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ " -ForegroundColor Magenta
Write-Host "░▒▓██████▓▒░░▒▓█▓▒░      ░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░ " -ForegroundColor Magenta
Write-Host "░▒▓█▓▒░     ░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ " -ForegroundColor DarkMagenta
Write-Host "░▒▓█▓▒░     ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ " -ForegroundColor DarkMagenta
Write-Host "░▒▓████████▓▒░▒▓██████▓▒░░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░  " -ForegroundColor DarkMagenta
Write-Host "========================================================" -ForegroundColor Gray
Write-Host "             INSTALLING XRL-CHAT SYSTEM                " -ForegroundColor Yellow
Write-Host "========================================================`n" -ForegroundColor Gray

$TargetDir = "$ENV:USERPROFILE\xrl-chat"
$LauncherName = "launcher_win.py"
$KeyEncName = "Server_1.enc"
$KeyOutName = "Server_1.json"

if (-not (Test-Path $TargetDir)) {
    New-Item -ItemType Directory -Path $TargetDir | Out-Null
}

Write-Host "[1/3] Downloading and decoding Firebase Key..." -ForegroundColor Cyan
$KeyEncUrl = "https://raw.githubusercontent.com/elernete10075/xrl/main/$KeyEncName"
$EncodedContent = (Invoke-WebRequest -Uri $KeyEncUrl -UseBasicParsing).Content.Trim()

# Декодирование из Base64 в корректный JSON-файл
$DecodedBytes = [System.Convert]::FromBase64String($EncodedContent)
$DecodedJson = [System.Text.Encoding]::UTF8.GetString($DecodedBytes)
Set-Content -Path "$TargetDir\$KeyOutName" -Value $DecodedJson -Encoding UTF8

Write-Host "[2/3] Downloading Windows Launcher..." -ForegroundColor Cyan
$LauncherUrl = "https://raw.githubusercontent.com/elernete10075/xrl/refs/heads/main/$LauncherName"
Invoke-WebRequest -Uri $LauncherUrl -OutFile "$TargetDir\$LauncherName" -UseBasicParsing

Write-Host "[3/3] Launching System..." -ForegroundColor Cyan
Start-Sleep -Seconds 1

Set-Location -Path $TargetDir
python "$TargetDir\$LauncherName"
