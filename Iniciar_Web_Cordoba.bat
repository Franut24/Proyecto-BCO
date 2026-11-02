@echo off
title Promociones Bancarias de Supermercados - Ciudad de Cordoba (Web)
cd /d "%~dp0"
echo ============================================================
echo   Iniciando Servidor Web (Ciudad de Cordoba)...
echo   Abriendo en tu navegador: http://127.0.0.1:5000
echo ============================================================
python run.py --web
pause
