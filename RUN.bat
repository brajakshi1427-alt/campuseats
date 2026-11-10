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
  echo Installing dependencies - needs internet only this first time...
  call npm install
  if errorlevel 1 (
    echo Dependency installation failed.
    pause
    exit /b 1
  )
)
node setup-env.js
if errorlevel 1 (
  pause
  exit /b 1
)
start "" http://localhost:4009
call npm start
pause
