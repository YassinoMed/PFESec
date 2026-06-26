# run_inference_server.ps1
# Lance le serveur d'inference GPU multi-modeles SecureRAG Hub

$scriptDir = $PSScriptRoot
Set-Location $scriptDir

$venvPy = Join-Path $scriptDir "..\myenv\Scripts\python.exe"
if (Test-Path $venvPy) {
    $pyExe = $venvPy
} else {
    $pyExe = "python"
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  SecureRAG Hub - Serveur GPU Multi-Modeles" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Interface web : http://localhost:8000/" -ForegroundColor Green
Write-Host "  API modeles   : http://localhost:8000/api/models" -ForegroundColor Green
Write-Host "  Statut GPU    : http://localhost:8000/api/gpu-status" -ForegroundColor Green
Write-Host ""
Write-Host "  Options :" -ForegroundColor Yellow
Write-Host "    --lazy          Charge les modeles a la demande" -ForegroundColor Gray
Write-Host "    --port <n>      Port (defaut : 8000)" -ForegroundColor Gray
Write-Host "    --models <ids>  Charge seulement ces modeles" -ForegroundColor Gray
Write-Host ""
Write-Host "  Demarrage du serveur..." -ForegroundColor Yellow
Write-Host ""

& $pyExe inference_server.py @args
