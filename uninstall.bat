@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0uninstall.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"
echo.
if not "%EXIT_CODE%"=="0" (
  echo Lit Review Construct uninstall failed with exit code %EXIT_CODE%.
  pause
  exit /b %EXIT_CODE%
)
pause
exit /b 0
