param(
    [double]$DatasetFraction = 1.0,
    [int]$DatasetSlice = 0
)

# Entraîne UNIQUEMENT les 2 modèles BERT (secbert + cysecbert) avec
# config "temps max". Les LLM (securityllm, phishsense) sont à lancer
# séparément ensuite via train_llm_long.ps1.
#
# Usage :
#   .\security\train_bert_long.ps1
#
# Logs : un fichier .log par modèle dans security\reports\

$ErrorActionPreference = "Continue"   # ne pas stopper si un modèle échoue
$python = Join-Path (Split-Path -Parent $PSScriptRoot) "myenv\Scripts\python.exe"
$pipeline = Join-Path $PSScriptRoot "train_adaptive_pipeline.py"

$reportsDir = Join-Path $PSScriptRoot "reports"
if (-not (Test-Path $reportsDir)) {
    New-Item -ItemType Directory -Path $reportsDir | Out-Null
}

function Run-Step {
    param([string]$name, [string[]]$extraArgs)

    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $log = Join-Path $reportsDir "train_$($name)_$stamp.log"
    $start = Get-Date

    Write-Host "`n============================================================" -ForegroundColor Cyan
    Write-Host "[$($start.ToString('HH:mm:ss'))] >>> $name" -ForegroundColor Cyan
    Write-Host "Log : $log" -ForegroundColor DarkGray
    Write-Host "============================================================" -ForegroundColor Cyan

    & $python $pipeline train --train $name --dataset-fraction $DatasetFraction --dataset-slice $DatasetSlice @extraArgs 2>&1 | Tee-Object -FilePath $log

    $end = Get-Date
    $dur = ($end - $start).ToString('hh\:mm\:ss')
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK ] $name terminé en $dur" -ForegroundColor Green
    } else {
        Write-Host "[KO ] $name a échoué (code=$LASTEXITCODE) après $dur" -ForegroundColor Red
    }
}

# Config commune aux 2 BERT — un seul endroit à modifier en cas d'OOM.
$bertArgs = @(
    "--bert-epochs", "15",
    "--bert-batch-size", "16",
    "--bert-max-samples", "0",
    "--bert-max-length", "512",
    "--bert-lr", "1e-5",
    "--no-early-stopping",
    "--logging-steps", "25",
    "--save-steps", "500"
)

# ============================================================
# 1) SecBERT
# ============================================================
Run-Step "secbert" $bertArgs

# ============================================================
# 2) CySecBERT
# ============================================================
Run-Step "cysecbert" $bertArgs

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Entraînements BERT terminés." -ForegroundColor Cyan
Write-Host "Logs : $reportsDir" -ForegroundColor DarkGray
Write-Host "Prochaine étape : lancer .\security\train_llm_long.ps1 pour les LLM." -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Cyan
