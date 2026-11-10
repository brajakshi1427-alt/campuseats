@echo off
setlocal
cd /d "%~dp0"
where node >nul 2>nul
if errorlevel 1 (
  echo Node.js is not installed. Install the LTS version from https://nodejs.org/
  pause
  exit /b 1
)
if not exist node_modules (
  echo Installing dependencies...
  call npm install
  if errorlevel 1 (
    pause
    exit /b 1
  )
)
node demo.js
echo.
echo Output also saved in demo-output.txt
pause
