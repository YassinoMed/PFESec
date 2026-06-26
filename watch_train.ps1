# watch_train.ps1
# Dashboard moderne et interactif pour suivre l'entraînement en temps réel.
#
# Usage :
#   .\watch_train.ps1
#

$ErrorActionPreference = "SilentlyContinue"
$OutputEncoding = [System.Text.Encoding]::UTF8

# Détecter le dossier racine du script
$scriptDir = $PSScriptRoot
$reportsDir = Join-Path $scriptDir "reports"

# Configuration des couleurs et styles de bordure
$borderColor = "Cyan"
$titleColor = "White"
$metricColor = "Yellow"
$successColor = "Green"
$runningColor = "Magenta"
$skippedColor = "DarkGray"

function Get-GPUStatus {
    if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
        $smi = nvidia-smi --query-gpu=utilization.gpu,temperature.gpu,memory.used,memory.total --format=csv,noheader,nounits
        $parts = $smi.Split(",")
        if ($parts.Count -ge 4) {
            $util = [int]$parts[0].Trim()
            $temp = [int]$parts[1].Trim()
            $memUsed = [float]$parts[2].Trim()
            $memTotal = [float]$parts[3].Trim()
            return @{
                Util = $util
                Temp = $temp
                MemUsed = [math]::Round($memUsed / 1024, 2)
                MemTotal = [math]::Round($memTotal / 1024, 2)
                MemPercent = [math]::Round(($memUsed / $memTotal) * 100, 1)
            }
        }
    }
    return $null
}

function Draw-ProgressBar {
    param(
        [int]$percent, 
        [int]$width = 22,
        [string]$filledChar = "#",
        [string]$emptyChar = "-"
    )
    $filled = [math]::Min($width, [math]::Max(0, [int]($percent / 100 * $width)))
    $empty = $width - $filled
    $bar = ($filledChar * $filled) + ($emptyChar * $empty)
    return $bar
}

# Charger les métriques déjà validées pour les afficher dans la table finale
function Get-CompletedMetrics {
    $metricsMap = @{}
    
    # 1. SecBERT et CySecBERT F1
    foreach ($model in @("secbert", "cysecbert")) {
        $outDir = Join-Path $scriptDir "outputs" "$model-phishing"
        $metaPath = Join-Path $outDir "training_meta.json"
        if (Test-Path $metaPath) {
            try {
                $meta = Get-Content $metaPath -Raw | ConvertFrom-Json
                if ($meta.metrics -and $meta.metrics.eval_f1) {
                    $metricsMap[$model] = [math]::Round($meta.metrics.eval_f1 * 100, 2)
                } elseif ($meta.metrics -and $meta.metrics.f1) {
                    $metricsMap[$model] = [math]::Round($meta.metrics.f1 * 100, 2)
                }
            } catch {}
        }
    }

    # 2. PhishSense F1
    $psMetaPath = Join-Path $scriptDir "outputs" "phishsense-targeted-lora" "training_meta.json"
    if (Test-Path $psMetaPath) {
        try {
            $meta = Get-Content $psMetaPath -Raw | ConvertFrom-Json
            if ($meta.metrics -and $meta.metrics.eval_f1) {
                $metricsMap["phishsense"] = [math]::Round($meta.metrics.eval_f1 * 100, 2)
            }
        } catch {}
    }
    
    return $metricsMap
}

# Boucle principale d'affichage
while ($true) {
    Clear-Host

    # 1. En-tête stylisé
    Write-Host "+--------------------------------------------------------------+" -ForegroundColor $borderColor
    Write-Host "|    *  SECURERAG HUB - INTERACTIVE PIPELINE MONITOR           |" -ForegroundColor $borderColor
    Write-Host "+--------------------------------------------------------------+" -ForegroundColor $borderColor

    # 2. Section GPU
    $gpu = Get-GPUStatus
    if ($gpu) {
        $gpuBar = Draw-ProgressBar $gpu.Util
        $vramBar = Draw-ProgressBar $gpu.MemPercent
        
        # Choix de la couleur pour la température
        $tempColor = "Green"
        if ($gpu.Temp -ge 78) { $tempColor = "Red" }
        elseif ($gpu.Temp -ge 65) { $tempColor = "Yellow" }

        Write-Host "  [ SYSTEM RESOURCES ]" -ForegroundColor White
        Write-Host "  |- GPU Load : [" -NoNewline -ForegroundColor White
        Write-Host "$gpuBar" -NoNewline -ForegroundColor Cyan
        Write-Host "] $($gpu.Util)%" -ForegroundColor White
        
        Write-Host "  |- VRAM     : [" -NoNewline -ForegroundColor White
        Write-Host "$vramBar" -NoNewline -ForegroundColor Green
        Write-Host "] $($gpu.MemUsed) GB / $($gpu.MemTotal) GB ($($gpu.MemPercent)%)" -ForegroundColor White

        Write-Host "  \- Temp.    : " -NoNewline -ForegroundColor White
        Write-Host "$($gpu.Temp)°C" -ForegroundColor $tempColor
    } else {
        Write-Host "  [GPU] NVIDIA GPU non détecté via nvidia-smi." -ForegroundColor Red
    }
    Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray

    # 3. Analyser les logs récents pour détecter l'état du pipeline
    $logFiles = Get-ChildItem -Path $reportsDir -Filter "train_*.log" | Sort-Object LastWriteTime -Descending
    
    $modelStates = @{
        "secbert" = "PENDING"
        "cysecbert" = "PENDING"
        "securityllm" = "SKIPPED"
        "phishsense" = "PENDING"
    }
    
    # Charger les métriques d'évaluation déjà enregistrées dans les meta-fichiers
    $modelMetrics = Get-CompletedMetrics
    $activeModel = $null
    
    # Paramètres de progression de l'entraînement actif
    $p_phase = "Training"
    $p_percent = 0
    $p_stepCur = ""
    $p_stepTot = ""
    $p_elapsed = ""
    $p_eta = ""
    $p_speedVal = ""
    $p_speedUnit = ""
    $p_epochCur = ""
    $p_epochTot = ""
    $p_loss = "--"
    $p_lr = "--"

    foreach ($file in $logFiles) {
        $name = $file.Name
        $model = $null
        if ($name -match 'train_([a-zA-Z0-9]+)_') {
            $model = $Matches[1]
        }
        if ($null -eq $model -or -not $modelStates.ContainsKey($model)) { continue }

        # Si l'état de ce modèle est déjà résolu dans notre passe, on passe
        if ($modelStates[$model] -ne "PENDING" -and $modelStates[$model] -ne "SKIPPED") { continue }

        # Lire le contenu
        $content = Get-Content $file.FullName -Raw
        if ($content -match 'terminé en' -or $content -match 'BERT terminé' -or $content -match 'LoRA terminé') {
            $modelStates[$model] = "COMPLETED"
        } elseif ($content -match 'a échoué' -or $content -match 'FAILED') {
            $modelStates[$model] = "FAILED"
        } else {
            # Si le fichier a été modifié il y a moins de 3 minutes, le modèle est considéré en cours
            $diff = (Get-Date) - $file.LastWriteTime
            if ($diff.TotalMinutes -lt 3) {
                $modelStates[$model] = "RUNNING"
                $activeModel = $model
                
                # Lire les dernières lignes pour extraire les stats fines d'entraînement
                $tailLines = Get-Content $file.FullName -Tail 60
                foreach ($line in $tailLines) {
                    # Détecter la phase de tokenisation/map
                    if ($line -match 'Map:\s*(\d+)%\s*\|.*\|\s*(\d+)/(\d+)\s*\[(\d{2}:\d{2})<(\d{2}:\d{2})') {
                        $p_phase = "Tokenizing Dataset"
                        $p_percent = [int]$Matches[1]
                        $p_stepCur = $Matches[2]
                        $p_stepTot = $Matches[3]
                        $p_elapsed = $Matches[4]
                        $p_eta = $Matches[5]
                    }
                    # Détecter la phase d'entraînement (tqdm normal)
                    # Exemples:
                    # "  5%|#         | 35/718 [00:42<13:42,  1.20s/it, Epoch 0.39/8]"
                    elseif ($line -match '(\d+)%\s*\|.*\|?\s*(\d+)/(\d+)\s*\[(\d{2}:\d{2}(?::\d{2})?)<(\d{2}:\d{2}(?::\d{2})?),\s*([\d.]+)\s*(s/it|it/s)(?:,\s*Epoch\s*([\d.]+)/(\d+))?') {
                        $p_phase = "Finetuning Model"
                        $p_percent = [int]$Matches[1]
                        $p_stepCur = $Matches[2]
                        $p_stepTot = $Matches[3]
                        $p_elapsed = $Matches[4]
                        $p_eta = $Matches[5]
                        $p_speedVal = $Matches[6]
                        $p_speedUnit = $Matches[7]
                        if ($Matches[8]) { $p_epochCur = $Matches[8] }
                        if ($Matches[9]) { $p_epochTot = $Matches[9] }
                    }
                    # Détecter les logs JSON périodiques de perte / lr
                    # Exemple: {'loss': 0.0892, 'learning_rate': 6.54e-05, 'epoch': 1.34}
                    if ($line -match 'loss.:\s*([\d.]+)') {
                        $p_loss = $Matches[1]
                    }
                    if ($line -match 'learning_rate.:\s*([\d.e+-]+)') {
                        $p_lr = $Matches[1]
                    }
                    if ($line -match 'epoch.:\s*([\d.]+)') {
                        $p_epochCur = $Matches[1]
                    }
                }
            }
        }
    }

    # 4. Afficher la section d'entraînement actif
    if ($activeModel) {
        Write-Host "  [ ACTIVE TRAINING - $($activeModel.ToUpper()) ]" -ForegroundColor $runningColor
        
        $progressBar = Draw-ProgressBar $p_percent 30 "#" "-"
        
        Write-Host "  |- Phase     : " -NoNewline -ForegroundColor White
        Write-Host "$p_phase" -ForegroundColor Yellow
        
        Write-Host "  |- Progress  : [" -NoNewline -ForegroundColor White
        Write-Host "$progressBar" -NoNewline -ForegroundColor $runningColor
        Write-Host "] $p_percent%" -ForegroundColor White

        if ($p_stepCur -and $p_stepTot) {
            Write-Host "  |- Step      : $p_stepCur / $p_stepTot" -ForegroundColor White
        }
        if ($p_epochCur) {
            $epochStr = "$p_epochCur"
            if ($p_epochTot) { $epochStr += " / $p_epochTot" }
            Write-Host "  |- Epoch     : $epochStr" -ForegroundColor White
        }
        if ($p_elapsed -or $p_eta) {
            Write-Host "  |- Time      : Elapsed: $p_elapsed | Remaining (ETA): $p_eta" -ForegroundColor White
        }
        if ($p_speedVal) {
            Write-Host "  |- Speed     : $p_speedVal $p_speedUnit" -ForegroundColor White
        }
        
        # Affichage des métriques d'apprentissage
        Write-Host "  \- Metrics   : " -NoNewline -ForegroundColor White
        Write-Host "Loss: " -NoNewline -ForegroundColor DarkGray
        Write-Host "$p_loss" -NoNewline -ForegroundColor $metricColor
        Write-Host " | " -NoNewline -ForegroundColor DarkGray
        Write-Host "LR: " -NoNewline -ForegroundColor DarkGray
        Write-Host "$p_lr" -ForegroundColor $metricColor
        
    } else {
        Write-Host "  [ ACTIVE TRAINING ]" -ForegroundColor White
        Write-Host "  \- Status    : " -NoNewline -ForegroundColor White
        Write-Host "Idle (Aucun entraînement actif détecté)" -ForegroundColor Green
    }
    Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray

    # 5. Afficher la table récapitulative des modèles de la pipeline
    Write-Host "  [ PIPELINE SUMMARY ]" -ForegroundColor White
    
    $models = @("secbert", "cysecbert", "securityllm", "phishsense")
    foreach ($m in $models) {
        $state = $modelStates[$m]
        
        # Par défaut
        $color = "DarkGray"
        $statusStr = "[$state]"
        $metricStr = ""

        # Déterminer les détails selon l'état
        switch ($state) {
            "COMPLETED" { 
                $color = "Green"
                $statusStr = "[OK] COMPLETED" 
            }
            "RUNNING" { 
                $color = "Magenta"
                $statusStr = "[RUNNING] ($p_percent%)" 
            }
            "FAILED" { 
                $color = "Red" 
                $statusStr = "[FAIL] FAILED" 
            }
            "SKIPPED" { 
                $color = "DarkGray"
                if ($m -eq "securityllm") {
                    $statusStr = "[SKIP] EXCLUDED (7B Model)"
                } else {
                    $statusStr = "[SKIP] Already Trained"
                }
            }
            "PENDING" { 
                $color = "Blue"
                $statusStr = "[WAIT] PENDING" 
            }
        }

        # Ajouter le score F1-Score si présent
        if ($modelMetrics.ContainsKey($m)) {
            $metricStr = "  [F1-Score: $($modelMetrics[$m])%]"
        }

        # Formatter joliment les colonnes
        $mFormatted = $m.PadRight(15)
        $statusFormatted = $statusStr.PadRight(28)
        
        Write-Host "  |- " -NoNewline -ForegroundColor DarkGray
        Write-Host "$mFormatted" -NoNewline -ForegroundColor White
        Write-Host "->  " -NoNewline -ForegroundColor DarkGray
        Write-Host "$statusFormatted" -NoNewline -ForegroundColor $color
        Write-Host "$metricStr" -ForegroundColor DarkGreen
    }

    Write-Host "----------------------------------------------------------------" -ForegroundColor DarkGray
    Write-Host "  Mise à jour automatique toutes les 3s. Ctrl+C pour quitter." -ForegroundColor DarkGray

    Start-Sleep -Seconds 3
}
