@echo off
chcp 65001 >nul
title SecureRAG Hub - Deploiement Nginx + Backend
color 0B

echo.
echo ========================================================
echo   SecureRAG Hub -- Deploiement Public avec Nginx
echo ========================================================
echo   Frontend : Nginx - ai-soc-web/out/ (port 80)
echo   Backend  : inference_server.py (port 8000)
echo   API      : /api/* - proxy vers le backend
echo ========================================================
echo.

:: -- Variables --
set SCRIPT_DIR=%~dp0
set NGINX_DIR=C:\nginx
set NGINX_CONF=%SCRIPT_DIR%nginx.conf
set VENV_PY=%SCRIPT_DIR%..\myenv\Scripts\python.exe

:: -- Verification de Nginx --
if not exist "%NGINX_DIR%\nginx.exe" (
    echo   [ERREUR] Nginx non trouve dans %NGINX_DIR%
    echo.
    echo   Telechargez Nginx pour Windows depuis :
    echo     https://nginx.org/en/download.html
    echo   Puis extrayez-le dans %NGINX_DIR%\
    echo.
    pause
    exit /b 1
)

echo   [OK] Nginx trouve : %NGINX_DIR%\nginx.exe

:: -- Verification du Python --
if exist "%VENV_PY%" (
    echo   [OK] VirtualEnv Python : %VENV_PY%
    set PYTHON=%VENV_PY%
) else (
    echo   [INFO] VirtualEnv non trouve, utilisation de python systeme
    set PYTHON=python
)

:: -- Copie de la config Nginx --
echo.
echo   Copie de la configuration Nginx...
copy /Y "%NGINX_CONF%" "%NGINX_DIR%\conf\nginx.conf" >nul
if errorlevel 1 (
    echo   [ERREUR] Impossible de copier nginx.conf
    echo   Essayez d'executer ce script en tant qu'Administrateur.
    pause
    exit /b 1
)
echo   [OK] nginx.conf copie dans %NGINX_DIR%\conf\

:: -- Arret des instances precedentes --
echo.
echo   Arret des instances precedentes...
taskkill /F /IM nginx.exe 2>nul
taskkill /F /IM python.exe 2>nul
echo   [OK] Instances Nginx et Python arretees

:: -- Demarrage des Backends Python --
echo.
echo   Demarrage du backend d'inference (port 8000)...
start "SecureRAG Inference" /MIN "%PYTHON%" "%SCRIPT_DIR%inference_server.py" --port 8000
echo   [OK] Inference Server demarre en arriere-plan

echo   Demarrage de l'orchestrateur de securite (port 8080)...
start "SecureRAG Orchestrator" /MIN "%PYTHON%" "%SCRIPT_DIR%backend\main.py"
echo   [OK] Orchestrator Server demarre en arriere-plan

:: Attendre un peu que les backends s'initialisent
echo   Attente du demarrage des backends (5s)...
timeout /t 5 /nobreak >nul

:: -- Verification des backends --
echo.
echo   Verification des backends...
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8000/api/models' -UseBasicParsing -TimeoutSec 10; if ($r.StatusCode -eq 200) { Write-Host '  [OK] Inference Server repond sur le port 8000' } else { Write-Host '  [WARN] Inference Server repond avec status' $r.StatusCode } } catch { Write-Host '  [WARN] Inference Server pas encore pret (les modeles se chargent peut-etre)' }"
powershell -Command "try { $r = Invoke-WebRequest -Uri 'http://localhost:8080/health' -UseBasicParsing -TimeoutSec 10; if ($r.StatusCode -eq 200) { Write-Host '  [OK] Orchestrator Server repond sur le port 8080' } else { Write-Host '  [WARN] Orchestrator Server repond avec status' $r.StatusCode } } catch { Write-Host '  [WARN] Orchestrator Server pas encore pret' }"

:: -- Demarrage de Nginx --
echo.
echo   Demarrage de Nginx (port 80)...
cd /d "%NGINX_DIR%"
start nginx.exe

:: -- Test de la configuration --
echo.
"%NGINX_DIR%\nginx.exe" -t 2>&1
if errorlevel 1 (
    echo   [ERREUR] La configuration Nginx contient des erreurs !
    echo   Verifiez nginx.conf et reessayez.
    pause
    exit /b 1
)

echo   [OK] Nginx demarre avec succes !

:: -- Affichage des URL --
echo.
echo ========================================================
echo              SERVEUR EN LIGNE !
echo ========================================================
echo.
echo   Acces local :
echo     http://localhost/
echo     http://localhost/api/models
echo.
echo   Acces reseau local :

:: Afficher les IP locales
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /C:"IPv4"') do (
    echo     http://%%a/
)

echo.
echo   Pour l'acces externe, utilisez votre IP publique
echo   ou votre nom de domaine.
echo.
echo   Pour arreter : stop_nginx.cmd
echo ========================================================
echo.
echo Appuyez sur une touche pour fermer cette fenetre...
echo (Le serveur continuera de tourner en arriere-plan)
pause >nul
