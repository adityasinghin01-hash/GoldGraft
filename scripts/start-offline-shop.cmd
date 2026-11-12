@echo off
cd /d "%~dp0.."
"D:\DevTools\GoldGraft\switch-venv\Scripts\python.exe" pieces\shops\legacy-php-shop\local_shop.py
exit /b %errorlevel%
