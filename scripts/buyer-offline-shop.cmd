@echo off
cd /d "%~dp0.."
"D:\DevTools\GoldGraft\node-v22.23.4-win-x64\node.exe" pieces\shops\legacy-php-shop\buyer.mjs
exit /b %errorlevel%
