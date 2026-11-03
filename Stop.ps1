$ErrorActionPreference = "SilentlyContinue"
$p = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -like "*streamlit*run*app.py*" -and $_.CommandLine -like "*8765*"
}
foreach ($x in $p) { Stop-Process -Id $x.ProcessId -Force }
Write-Host "JARVIS QUANT AI dashboard process stopped. Existing Jarvis processes were not touched." -ForegroundColor Yellow
