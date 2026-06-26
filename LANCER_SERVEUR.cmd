@echo off
chcp 65001 >nul
title SecureRAG Hub - GPU Inference Server

set SCRIPT_DIR=%~dp0
set VENV_PY=%SCRIPT_DIR%..\myenv\Scripts\python.exe

echo.
echo ======================================================
echo   SecureRAG Hub - Serveur GPU Multi-Modeles
echo ======================================================
echo.
echo   Interface web : http://localhost:8000/
echo   API modeles   : http://localhost:8000/api/models
echo   Statut GPU    : http://localhost:8000/api/gpu-status
echo.

if exist "%VENV_PY%" (
    echo   [OK] VirtualEnv Python trouve : %VENV_PY%
    set PYTHON=%VENV_PY%
) else (
    echo   [INFO] VirtualEnv non trouve, utilisation de python systeme
    set PYTHON=python
)

echo.
echo   Options de lancement :
echo     1 - Charger TOUS les modeles en VRAM au demarrage [recommande]
echo     2 - Mode lazy ^(charge a la demande, economise VRAM^)
echo     3 - Seulement BERT ^(cysecbert + secbert, leger^)
echo.
set /p CHOICE="  Votre choix [1/2/3] (defaut: 1) : "

if "%CHOICE%"=="2" (
    echo.
    echo   Demarrage en mode lazy...
    "%PYTHON%" "%SCRIPT_DIR%inference_server.py" --lazy
) else if "%CHOICE%"=="3" (
    echo.
    echo   Demarrage avec seulement les modeles BERT...
    "%PYTHON%" "%SCRIPT_DIR%inference_server.py" --models cysecbert secbert
) else (
    echo.
    echo   Demarrage avec chargement complet en VRAM...
    "%PYTHON%" "%SCRIPT_DIR%inference_server.py"
)

pause
