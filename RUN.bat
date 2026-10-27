@echo off
cd /d "%~dp0"
if not exist node_modules call npm install
start /b cmd /c "timeout /t 4 >nul & start http://localhost:4000"
node server.js
