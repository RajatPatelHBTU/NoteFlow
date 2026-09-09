# NoteFlow Server Launcher
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Starting NoteFlow Development Server  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Access the app at: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server.`n" -ForegroundColor DarkGray

if (Test-Path "$ScriptDir\venv\Scripts\python.exe") {
    & "$ScriptDir\venv\Scripts\python.exe" -m uvicorn app.main:app --reload --port 8000
} else {
    Write-Host "Error: Virtual environment not found at $ScriptDir\venv" -ForegroundColor Red
}
