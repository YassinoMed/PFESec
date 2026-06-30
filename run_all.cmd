@echo off
chcp 65001 >nul
title SecureRAG Hub - Multi-Master AI
cd /d "%~dp0"

echo ==============================================================
echo   SecureRAG Hub — Architecture Multi-Master AI
echo ==============================================================
echo.
echo   Dashboard Multi-Master : http://localhost:8090/
echo   Interface Web          : http://localhost:8000/
echo   API Inference          : http://localhost:8080/
echo.
echo   Appuyez sur Ctrl+C pour arreter tous les serveurs
echo ==============================================================
echo.

:: Vérifier Python
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERREUR] Python introuvable dans le PATH
    pause
    exit /b 1
)

echo [1/3] Démarrage du Dashboard Multi-Master AI (port 8090)...
start "Dashboard" cmd /c "python backend/dashboard/server.py"
timeout /t 2 /nobreak >nul

echo [2/3] Démarrage du serveur Web (port 8000)...
start "WebServer" cmd /c "python web_server.py"
timeout /t 2 /nobreak >nul

echo [3/3] Démarrage du serveur d'inférence GPU (port 8080)...
start "InferenceServer" cmd /c "python inference_server.py --lazy"

echo.
echo ==============================================================
echo   TOUS LES SERVEURS SONT LANCES
echo ==============================================================
echo.
echo   Dashboard Multi-Master : http://localhost:8090/
echo   Interface Web          : http://localhost:8000/
echo   API Inference          : http://localhost:8080/
echo.
echo   Fermez cette fenêtre pour arreter les serveurs
echo ==============================================================
pause
