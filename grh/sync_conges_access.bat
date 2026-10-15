@echo off
REM Synchro des conges valides : Access (dbo_congevalides) -> PostgreSQL
REM Resultat dans logs\sync_conges_access.log
REM Chemins relatifs a ce .bat (dans back_rh\grh, Python dans back_rh\env)

set PROJET=%~dp0
set PYTHON=%~dp0..\env\Scripts\python.exe

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

cd /d "%PROJET%"
if not exist logs mkdir logs
echo. >> logs\sync_conges_access.log
echo ===== %date% %time% ===== >> logs\sync_conges_access.log
if not exist "%PYTHON%" (
  echo Python introuvable : %PYTHON% >> logs\sync_conges_access.log
  exit /b 1
)
"%PYTHON%" manage.py sync_conges_access >> logs\sync_conges_access.log 2>&1