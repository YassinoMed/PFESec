param(
    [double]$DatasetFraction = 1.0,
    [int]$DatasetSlice = 0
)

# Entraîne UNIQUEMENT les 2 modèles LLM (securityllm + phishsense)
# avec config "temps max". À lancer après train_bert_long.ps1 (ou
# indépendamment).
#
# Usage :
#   .\security\train_llm_long.ps1
#
# Logs : un fichier .log par modèle dans security\reports\

$ErrorActionPreference = "Continue"
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

# Config commune aux 2 LLM — un seul endroit à modifier en cas d'OOM.
$llmArgs = @(
    "--llm-epochs", "8",
    "--llm-batch-size", "1",
    "--grad-accum", "16",
    "--llm-lr", "1e-4",
    "--llm-max-length", "1024",
    "--lora-r", "32",
    "--lora-alpha", "64",
    "--lora-dropout", "0.05",
    "--max-samples", "0",
    "--no-early-stopping",
    "--logging-steps", "25",
    "--save-steps", "500"
)

# ============================================================
# 1) SecurityLLM
# ============================================================
Run-Step "securityllm" $llmArgs

# ============================================================
# 2) PhishSense
# ============================================================
Run-Step "phishsense" $llmArgs

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Entraînements LLM terminés." -ForegroundColor Cyan
Write-Host "Logs : $reportsDir" -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Cyan
