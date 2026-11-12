@echo off
cd /d "%~dp0.."
"D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe" scripts\check_all_local.py
exit /b %errorlevel%
