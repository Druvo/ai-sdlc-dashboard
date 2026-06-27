@echo off
echo.
echo  ========================================
echo   AI Intelligence Dashboard
echo  ========================================
echo  Starting on http://localhost:8501
echo  Press Ctrl+C to stop
echo  ========================================
echo.

cd /d "%~dp0"
python server.py
pause
