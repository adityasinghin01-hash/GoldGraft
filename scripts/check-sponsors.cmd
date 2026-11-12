@echo off
cd /d "%~dp0.."
"D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe" scripts\check_sponsor_assets.py
if errorlevel 1 exit /b %errorlevel%
"D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe" scripts\check_sponsor_examples.py --node "D:\DevTools\GoldGraft\node-v22.23.4-win-x64\node.exe"
exit /b %errorlevel%
