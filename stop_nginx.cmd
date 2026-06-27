@echo off
chcp 65001 >nul
title SecureRAG Hub - Arret des services
color 0C

echo.
echo ========================================================
echo     SecureRAG Hub -- Arret des services
echo ========================================================
echo.

:: -- Arret de Nginx --
echo   Arret de Nginx...
set NGINX_DIR=C:\nginx

if exist "%NGINX_DIR%\nginx.exe" (
    cd /d "%NGINX_DIR%"
    nginx.exe -s quit 2>nul
    timeout /t 2 /nobreak >nul
    :: Forcer l'arret si quit n'a pas fonctionne
    taskkill /F /IM nginx.exe 2>nul
    echo   [OK] Nginx arrete
) else (
    taskkill /F /IM nginx.exe 2>nul
    echo   [OK] Processus Nginx termines
)

:: -- Arret des Backends Python --
echo.
set /p KILL_BACKEND="  Arreter aussi les backends Python (inference + orchestrator) ? [O/N] (defaut: O) : "
if /I "%KILL_BACKEND%"=="N" (
    echo   [INFO] Backends Python laisses en cours d'execution
) else (
    echo   Arret des backends Python...
    :: Chercher le processus Python qui execute inference_server.py ou main.py
    powershell -Command "Get-Process python*, pythonw* -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*inference_server*' -or $_.CommandLine -like '*backend\main.py*' -or $_.CommandLine -like '*backend/main.py*' } | Stop-Process -Force -ErrorAction SilentlyContinue"
    :: Fallback : tuer par titre de fenetre
    taskkill /FI "WINDOWTITLE eq SecureRAG Inference" /F 2>nul
    taskkill /FI "WINDOWTITLE eq SecureRAG Orchestrator" /F 2>nul
    echo   [OK] Backends Python arretes
)

echo.
echo ========================================================
echo       Tous les services sont arretes
echo ========================================================
echo.
pause
