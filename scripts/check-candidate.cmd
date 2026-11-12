@echo off
cd /d "%~dp0.."
"D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe" scripts\check_candidate.py
if errorlevel 1 exit /b %errorlevel%
"D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe" scripts\check_candidate_browser.py
exit /b %errorlevel%
