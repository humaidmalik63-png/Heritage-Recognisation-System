@echo off
title Indian Heritage & Monument Verification Platform - Launcher
cls
echo ==============================================================================
echo   PROJECT NO. 30: VISUAL HERITAGE RECOGNITION PLATFORM (SIH 2025 SIH25052)
echo   Two-Tier Hybrid Architecture (CLIP + FAISS Vector Search + Gemini 2.5 Flash)
echo ==============================================================================
echo.

cd /d "%~dp0"

:: Check virtual environment
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Python virtual environment not found in .venv.
    echo Please create the virtual environment and install requirements first.
    pause
    exit /b 1
)

echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "Heritage API - FastAPI Server (Port 8000)" cmd /k "cd /d ""%~dp0"" && echo Starting Backend... && .venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"

timeout /t 3 /nobreak >nul

echo [2/2] Launching React (Vite) Frontend on http://127.0.0.1:5173 ...
start "Heritage Web UI - Vite Frontend (Port 5173)" cmd /k "cd /d ""%~dp0frontend"" && echo Starting Frontend... && npm run dev"

echo.
echo ==============================================================================
echo   PLATFORM SERVICES RUNNING CONCURRENTLY:
echo   - Web Application:       http://localhost:5173
echo   - Backend REST API:      http://localhost:8000
echo   - Interactive API Docs:  http://localhost:8000/docs
echo   - Exceptions Endpoint:   http://localhost:8000/api/exceptions
echo.
echo   Demo Curator Credentials:
echo     Email:    curator@asi.gov.in
echo     Password: password123 (or any 6+ char password on signup)
echo ==============================================================================
echo Both server windows have been launched. Keep this window or close it at will.
echo.
pause

