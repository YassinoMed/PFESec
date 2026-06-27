@echo off
chcp 65001 >nul
title SecureRAG Hub - Configuration Pare-feu
color 0E

echo.
echo ========================================================
echo   SecureRAG Hub -- Configuration du Pare-feu Windows
echo   Ce script doit etre execute en tant qu'Administrateur !
echo ========================================================
echo.

:: -- Verification des droits admin --
net session >nul 2>&1
if errorlevel 1 (
    echo   [ERREUR] Ce script necessite les droits Administrateur !
    echo.
    echo   Clic droit sur le fichier - "Executer en tant qu'administrateur"
    echo.
    pause
    exit /b 1
)

echo   [OK] Droits administrateur confirmes
echo.

:: -- Regle HTTP (port 80) --
echo   Ajout de la regle pare-feu pour HTTP (port 80)...
netsh advfirewall firewall add rule name="SecureRAG Hub - Nginx HTTP" dir=in action=allow protocol=TCP localport=80 description="Autorise l'acces HTTP pour SecureRAG Hub via Nginx"

if errorlevel 1 (
    echo   [ERREUR] Echec de l'ajout de la regle HTTP
) else (
    echo   [OK] Port 80 (HTTP) ouvert
)

echo.

:: -- Regle HTTPS (port 443) --
set /p HTTPS_RULE="  Ouvrir aussi le port 443 (HTTPS) ? [O/N] (defaut: N) : "
if /I "%HTTPS_RULE%"=="O" (
    echo   Ajout de la regle pare-feu pour HTTPS (port 443)...
    netsh advfirewall firewall add rule name="SecureRAG Hub - Nginx HTTPS" dir=in action=allow protocol=TCP localport=443 description="Autorise l'acces HTTPS pour SecureRAG Hub via Nginx"

    if errorlevel 1 (
        echo   [ERREUR] Echec de l'ajout de la regle HTTPS
    ) else (
        echo   [OK] Port 443 (HTTPS) ouvert
    )
) else (
    echo   [INFO] Port 443 non ouvert (HTTPS)
)

echo.
echo ========================================================
echo        Pare-feu configure avec succes !
echo ========================================================
echo.
echo   Regles ajoutees :
echo     - SecureRAG Hub - Nginx HTTP (port 80, entrant)
echo.
echo   Pour supprimer ces regles plus tard :
echo     netsh advfirewall firewall delete rule name="SecureRAG Hub - Nginx HTTP"
echo.
echo   N'oubliez pas la redirection de port sur votre
echo   routeur/box Internet !
echo.
pause
