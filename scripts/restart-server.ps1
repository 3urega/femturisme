# Stop zombie Flask/python listeners on 5010 and start a single clean server.
$ErrorActionPreference = 'SilentlyContinue'
$port = if ($env:PORT) { [int]$env:PORT } else { 5010 }

Write-Host "Stopping listeners on port $port..."
Get-NetTCPConnection -LocalPort $port -State Listen | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force
}

Start-Sleep -Seconds 2

$env:AGENT_USE_RELOADER = '0'
$env:FLASK_DEBUG = '0'
Set-Location (Split-Path $PSScriptRoot -Parent)
Write-Host "Starting python main.py (no reloader)..."
python main.py
