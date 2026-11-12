@echo off
cd /d "%~dp0.."
call scripts\check-all-local.cmd
if errorlevel 1 exit /b %errorlevel%
"D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe" scripts\check_team_boundaries.py
if errorlevel 1 exit /b %errorlevel%
"D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe" scripts\check_shop_integration.py
if errorlevel 1 exit /b %errorlevel%
"D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe" scripts\build_local_handoff.py
exit /b %errorlevel%
