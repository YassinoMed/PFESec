@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM Entraine les 4 modeles l'un apres l'autre, config "temps max".
REM Chaque modele a son propre log dans security\reports\.
REM Si un modele echoue, les suivants tournent quand meme.
REM
REM Usage :
REM   security\train_all.cmd
REM ============================================================

set "PYTHON=.\myenv\Scripts\python.exe"
set "PIPELINE=.\security\train_adaptive_pipeline.py"
set "REPORTS=.\security\reports"

if not exist "%REPORTS%" mkdir "%REPORTS%"

REM Horodatage commun a toute la session.
set "TS=%date:~-4%%date:~3,2%%date:~0,2%-%time:~0,2%%time:~3,2%%time:~6,2%"
set "TS=%TS: =0%"
set "SUMMARY=%REPORTS%\train_all_%TS%.summary.log"
type nul > "%SUMMARY%"

REM Args partages — un seul endroit a modifier en cas d'OOM.
set "BERT_ARGS=--bert-epochs 15 --bert-batch-size 16 --bert-max-samples 0 --bert-max-length 512 --bert-lr 1e-5 --no-early-stopping --logging-steps 25 --save-steps 500"
set "LLM_ARGS=--llm-epochs 8 --llm-batch-size 1 --grad-accum 16 --llm-lr 1e-4 --llm-max-length 1024 --lora-r 32 --lora-alpha 64 --lora-dropout 0.05 --max-samples 0 --no-early-stopping --logging-steps 25 --save-steps 500"

echo ============================================================
echo Entrainement complet : 4 modeles
echo Demarrage : %date% %time%
echo Resume    : %SUMMARY%
echo ============================================================

call :run_step secbert      "%BERT_ARGS%"
call :run_step cysecbert    "%BERT_ARGS%"
call :run_step securityllm  "%LLM_ARGS%"
call :run_step phishsense   "%LLM_ARGS%"

echo.
echo ============================================================
echo Tous les entrainements sont termines.
echo Fin    : %date% %time%
echo Resume :
type "%SUMMARY%"
echo ============================================================

endlocal
exit /b 0


REM ============================================================
REM Sous-routine : lance UN modele, log dedie, continue sur erreur.
REM Usage : call :run_step ^<nom^> "^<args completes^>"
REM ============================================================
:run_step
set "MODEL=%~1"
set "STEP_ARGS=%~2"

set "STEP_TS=%date:~-4%%date:~3,2%%date:~0,2%-%time:~0,2%%time:~3,2%%time:~6,2%"
set "STEP_TS=!STEP_TS: =0!"
set "LOG=%REPORTS%\train_!MODEL!_!STEP_TS!.log"

echo.
echo ============================================================
echo [%time%] ^>^>^> !MODEL!
echo Log : !LOG!
echo ============================================================

REM En-tete du log.
echo Commande  : %PYTHON% %PIPELINE% train --train !MODEL! !STEP_ARGS!  > "!LOG!"
echo Demarrage : %date% %time%                                          >> "!LOG!"
echo ============================================================      >> "!LOG!"

%PYTHON% %PIPELINE% train --train !MODEL! !STEP_ARGS! >> "!LOG!" 2>&1
set "RC=!errorlevel!"

echo ============================================================ >> "!LOG!"
echo Fin       : %date% %time% (code=!RC!)                        >> "!LOG!"

if !RC! equ 0 (
    echo [OK ] !MODEL!  code=0  log=!LOG!
    echo [OK ] !MODEL!  code=0  log=!LOG! >> "%SUMMARY%"
) else (
    echo [KO ] !MODEL!  code=!RC!  log=!LOG!
    echo [KO ] !MODEL!  code=!RC!  log=!LOG! >> "%SUMMARY%"
)

goto :eof
