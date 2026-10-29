@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ===================================================================
rem  Database Backup Script for MySQL crm_db
rem  Usage: scripts\backup.bat
rem ===================================================================

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%.."
set "PROJECT_ROOT=%CD%"
popd

rem --- 1. Try running via Project Backup Service (Python) ---
set "PYTHON_EXE="
if exist "%PROJECT_ROOT%\.venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%\.venv\Scripts\python.exe"
) else if exist "%PROJECT_ROOT%\venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%\venv\Scripts\python.exe"
) else (
    for %%X in (python.exe) do (
        set "PYTHON_EXE=%%~$PATH:X"
    )
)

if not "%PYTHON_EXE%"=="" (
    "%PYTHON_EXE%" -c "import os, sys, django; from pathlib import Path; ROOT = Path(r'%PROJECT_ROOT%'); sys.path.insert(0, str(ROOT)); os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings'); django.setup(); from apps.admin_portal.services.backup_service import create_database_backup; p = create_database_backup(purpose='script_backup'); print(f'[SUCCESS] Backup completed successfully.\nBackup file : {p}\nFile size   : {p.stat().st_size} bytes')"
    if !ERRORLEVEL! equ 0 (
        exit /b 0
    )
    echo [WARNING] Python backup service encountered an error. Attempting standalone fallback...
)

rem --- 2. Standalone Fallback: Read configuration from .env ---
set "ENV_FILE=%PROJECT_ROOT%\.env"
if exist "%ENV_FILE%" (
    for /f "usebackq eol=# tokens=1,* delims==" %%A in ("%ENV_FILE%") do (
        set "KEY=%%A"
        set "VAL=%%B"
        for /f "tokens=* delims= " %%K in ("!KEY!") do set "KEY=%%K"
        if not "!VAL!"=="" (
            for /f "tokens=* delims= " %%V in ("!VAL!") do set "VAL=%%V"
            if "!VAL:~0,1!"=="\"" if "!VAL:~-1!"=="\"" set "VAL=!VAL:~1,-1!"
            if "!VAL:~0,1!"=="'" if "!VAL:~-1!"=="'" set "VAL=!VAL:~1,-1!"
        )
        if "!KEY!"=="DB_NAME" if "%DB_NAME%"=="" set "DB_NAME=!VAL!"
        if "!KEY!"=="DB_USER" if "%DB_USER%"=="" set "DB_USER=!VAL!"
        if "!KEY!"=="DB_PASSWORD" if "%DB_PASSWORD%"=="" set "DB_PASSWORD=!VAL!"
        if "!KEY!"=="DB_HOST" if "%DB_HOST%"=="" set "DB_HOST=!VAL!"
        if "!KEY!"=="DB_PORT" if "%DB_PORT%"=="" set "DB_PORT=!VAL!"
        if "!KEY!"=="MYSQL_BIN" if "%MYSQL_BIN%"=="" set "MYSQL_BIN=!VAL!"
    )
)

if "%DB_HOST%"=="" set "DB_HOST=127.0.0.1"
if "%DB_PORT%"=="" set "DB_PORT=3306"

if "%DB_NAME%"=="" (
    echo [ERROR] DB_NAME is not configured in environment or .env.
    exit /b 1
)
if "%DB_USER%"=="" (
    echo [ERROR] DB_USER is not configured in environment or .env.
    exit /b 1
)

set "MYSQLDUMP_EXE="
if not "%MYSQL_BIN%"=="" (
    set "CLEAN_BIN=%MYSQL_BIN:"=%"
    if exist "!CLEAN_BIN!\mysqldump.exe" (
        set "MYSQLDUMP_EXE=!CLEAN_BIN!\mysqldump.exe"
    )
)
if "%MYSQLDUMP_EXE%"=="" (
    for %%X in (mysqldump.exe) do (
        set "MYSQLDUMP_EXE=%%~$PATH:X"
    )
)
if "%MYSQLDUMP_EXE%"=="" (
    echo [ERROR] mysqldump.exe was not found in MYSQL_BIN or system PATH.
    exit /b 1
)

set "BACKUP_DIR=%PROJECT_ROOT%\database\backups"
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%" 2>nul
)

for /f "usebackq" %%T in (`powershell -NoProfile -Command "Get-Date -Format 'yyyyMMdd_HHmmss'" 2^>nul`) do set "TIMESTAMP=%%T"
if "%TIMESTAMP%"=="" (
    set "TIMESTAMP=%DATE:~10,4%%DATE:~4,2%%DATE:~7,2%_%TIME:~0,2%%TIME:~3,2%%TIME:~6,2%"
    set "TIMESTAMP=!TIMESTAMP: =0!"
)

set "BACKUP_FILE=%BACKUP_DIR%\%DB_NAME%_%TIMESTAMP%.sql"
set "PARTIAL_FILE=%BACKUP_FILE%.partial"

echo Starting standalone database backup...
echo Database : %DB_NAME%
echo Output   : %BACKUP_FILE%

set "MYSQL_PWD=%DB_PASSWORD%"
pushd "%BACKUP_DIR%"
"%MYSQLDUMP_EXE%" --single-transaction --quick --no-tablespaces --default-character-set=utf8mb4 --set-gtid-purged=OFF --routines --events --triggers --host=%DB_HOST% --port=%DB_PORT% --user=%DB_USER% "%DB_NAME%" 1> "%PARTIAL_FILE%" 2> backup_err.log
set "DUMP_EXIT=!ERRORLEVEL!"
set "MYSQL_PWD="
popd

if !DUMP_EXIT! neq 0 (
    echo [ERROR] mysqldump failed with exit code !DUMP_EXIT!.
    if exist "%BACKUP_DIR%\backup_err.log" (
        type "%BACKUP_DIR%\backup_err.log"
        del /f /q "%BACKUP_DIR%\backup_err.log" 2>nul
    )
    if exist "%PARTIAL_FILE%" del /f /q "%PARTIAL_FILE%" 2>nul
    exit /b !DUMP_EXIT!
)
if exist "%BACKUP_DIR%\backup_err.log" del /f /q "%BACKUP_DIR%\backup_err.log" 2>nul

if not exist "%PARTIAL_FILE%" (
    echo [ERROR] Backup output was not created.
    exit /b 1
)

for %%F in ("%PARTIAL_FILE%") do set "BACKUP_SIZE=%%~zF"
move /y "%PARTIAL_FILE%" "%BACKUP_FILE%" >nul 2>&1

echo [SUCCESS] Backup completed successfully.
echo Backup file : %BACKUP_FILE%
echo File size   : !BACKUP_SIZE! bytes
exit /b 0
