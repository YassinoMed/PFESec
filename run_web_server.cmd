@echo off
title SecureRAG Hub - Web Server
cd /d "%~dp0"
echo ==============================================================
echo   Lancement du serveur de test de securite
echo   Site accessible sur : http://localhost:8000/
echo ==============================================================
python web_server.py
pause
