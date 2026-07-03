@echo off
cd /d "%~dp0"
echo.
echo Ejecutando build de documentacion...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\build-docs.ps1"
echo.
pause
