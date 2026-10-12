@echo off
rem Universal Computer CLI wrapper (host-neutral).
rem Resolves Core home: env UNIVERSAL_COMPUTER_HOME > scripts\core_path.txt
rem Resolves python: env UNIVERSAL_COMPUTER_PYTHON > PATH python
setlocal EnableDelayedExpansion
set "SCRIPT_DIR=%~dp0"
set "UC_PY=%UNIVERSAL_COMPUTER_PYTHON%"
if "%UC_PY%"=="" set "UC_PY=python"
set "UC_HOME=%UNIVERSAL_COMPUTER_HOME%"
if "%UC_HOME%"=="" (
  if exist "%SCRIPT_DIR%core_path.txt" (
    set /p UC_HOME=<"%SCRIPT_DIR%core_path.txt"
  )
)
if "%UC_HOME%"=="" (
  echo {"success": false, "error": {"type": "PROVIDER_UNAVAILABLE", "phase": "bootstrap", "retryable": false, "degrade_allowed": false, "raw": "UC_HOME not resolved: set UNIVERSAL_COMPUTER_HOME or run sync_skill.py"}}
  exit /b 1
)
"%UC_PY%" "%UC_HOME%\uc.py" %*
