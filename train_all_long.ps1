param(
    [double]$DatasetFraction = 1.0,
    [double]$DatasetStart = 0.0,
    [int]$DatasetSlice = 0,
    [switch]$SkipExisting
)

# Entraîne les 4 modèles l'un après l'autre, avec config "temps max".
# Chaque commande est isolée dans son propre process Python : si l'un
# échoue (OOM, dataset manquant…), les suivants tournent quand même.
#
# Usage :
#   .\security\train_all_long.ps1
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

    $runArgs = @()
    if ($SkipExisting) { $runArgs += "--skip-existing" }

    & $python $pipeline train --train $name --dataset-start $DatasetStart --dataset-fraction $DatasetFraction --dataset-slice $DatasetSlice @runArgs @extraArgs 2>&1 | Tee-Object -FilePath $log

    $end = Get-Date
    $dur = ($end - $start).ToString('hh\:mm\:ss')
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK ] $name terminé en $dur" -ForegroundColor Green
    } else {
        Write-Host "[KO ] $name a échoué (code=$LASTEXITCODE) après $dur" -ForegroundColor Red
    }
}

# ============================================================
# 1) SecBERT  — BERT classifier
# ============================================================
Run-Step "secbert" @(
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
# 2) CySecBERT  — BERT classifier
# ============================================================
Run-Step "cysecbert" @(
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
# 3) SecurityLLM  — LLM + LoRA (Exclu : Modèle 7B)
# ============================================================
# Run-Step "securityllm" @(
#     "--llm-epochs", "8",
#     "--llm-batch-size", "1",
#     "--grad-accum", "16",
#     "--llm-lr", "1e-4",
#     "--llm-max-length", "1024",
#     "--lora-r", "32",
#     "--lora-alpha", "64",
#     "--lora-dropout", "0.05",
#     "--max-samples", "0",
#     "--no-early-stopping",
#     "--logging-steps", "25",
#     "--save-steps", "500"
# )

# ============================================================
# 4) PhishSense  — LLM + LoRA
# ============================================================
Run-Step "phishsense" @(
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

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "Tous les entraînements sont terminés." -ForegroundColor Cyan
Write-Host "Logs : $reportsDir" -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Cyan
