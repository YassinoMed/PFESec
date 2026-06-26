# run_web_server.ps1
# Lance le serveur web de test de sécurité interactif.

$scriptDir = $PSScriptRoot
Set-Location $scriptDir

Write-Host "==============================================================" -ForegroundColor Cyan
Write-Host "  Lancement du serveur de test de sécurité interactif" -ForegroundColor Cyan
Write-Host "  Site disponible sur : http://localhost:8000/" -ForegroundColor Green
Write-Host "==============================================================" -ForegroundColor Cyan

python web_server.py
