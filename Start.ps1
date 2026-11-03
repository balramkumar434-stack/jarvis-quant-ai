$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (!(Test-Path ".venv\Scripts\python.exe")) {
    py -3.12 -m venv .venv
}
& ".venv\Scripts\python.exe" -m pip install --upgrade pip
& ".venv\Scripts\python.exe" -m pip install -r requirements.txt
if (!(Test-Path ".env")) { Copy-Item ".env.example" ".env" }
New-Item -ItemType Directory -Force -Path "data","logs" | Out-Null
Start-Process -FilePath ".venv\Scripts\python.exe" -ArgumentList "-m","streamlit","run","app.py","--server.address","127.0.0.1","--server.port","8765" -WorkingDirectory $PSScriptRoot -WindowStyle Normal
Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:8765"
Write-Host "JARVIS QUANT AI started. Dashboard: http://127.0.0.1:8765" -ForegroundColor Green
