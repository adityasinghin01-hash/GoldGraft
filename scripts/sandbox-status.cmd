@echo off
cd /d "%~dp0.."
python scripts\sandbox_config.py
exit /b %errorlevel%
