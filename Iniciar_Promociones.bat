@echo off
title Promociones Bancarias de Supermercados
cd /d "%~dp0"
echo ============================================================
echo   Iniciando Promociones Bancarias de Supermercados...
echo ============================================================
python run.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Hubo un problema al iniciar la aplicacion.
    echo Asegurate de tener Python instalado y accesible.
    pause
)
