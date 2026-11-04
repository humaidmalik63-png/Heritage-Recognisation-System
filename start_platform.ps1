# PowerShell Startup Script for Indian Heritage & Monument Verification Platform
# Project No. 30 (SIH 2025 SIH25052)

$Host.UI.RawUI.WindowTitle = "Indian Heritage Platform - Launcher"
Clear-Host

Write-Host "==============================================================================" -ForegroundColor DarkYellow
Write-Host "  PROJECT NO. 30: VISUAL HERITAGE RECOGNITION PLATFORM (SIH 2025 SIH25052)" -ForegroundColor Yellow
Write-Host "  Two-Tier Hybrid Architecture (CLIP + FAISS Vector Search + Gemini 2.5 Flash)" -ForegroundColor White
Write-Host "==============================================================================" -ForegroundColor DarkYellow
Write-Host ""

$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $baseDir ".venv\Scripts\python.exe"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python virtual environment not found at $pythonExe. Please configure .venv first."
    exit 1
}

Write-Host "[1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$baseDir'; & '$pythonExe' -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 3

Write-Host "[2/2] Launching React (Vite) Frontend on http://127.0.0.1:5173 ..." -ForegroundColor Cyan
$frontendDir = Join-Path $baseDir "frontend"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendDir'; npm run dev"

Write-Host ""
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host "  PLATFORM SERVICES ACTIVE:" -ForegroundColor White
Write-Host "  - Web Application:       http://localhost:5173" -ForegroundColor Yellow
Write-Host "  - Backend REST API:      http://localhost:8000" -ForegroundColor Yellow
Write-Host "  - Interactive API Docs:  http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  - Exceptions Endpoint:   http://localhost:8000/api/exceptions" -ForegroundColor Yellow
Write-Host "==============================================================================" -ForegroundColor Green
Write-Host ""

