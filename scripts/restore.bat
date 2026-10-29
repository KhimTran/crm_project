@echo off
setlocal EnableExtensions EnableDelayedExpansion

rem ===================================================================
rem  Database Restore Script for MySQL crm_db
rem  Usage: scripts\restore.bat <backup_file.sql> [--yes | --non-interactive]
rem ===================================================================

set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%.."
set "PROJECT_ROOT=%CD%"
popd

rem --- 1. Validate argument ---
set "BACKUP_ARG=%~1"
if "%BACKUP_ARG%"=="" (
    echo [ERROR] Missing required backup file argument.
    echo.
    echo Usage:
    echo   %~nx0 ^<path_to_backup.sql^> [--yes ^| --non-interactive]
    echo.
    echo Example:
    echo   %~nx0 database\backups\crm_db_example.sql
    exit /b 1
)

rem Resolve full path
set "BACKUP_FILE="
if exist "%BACKUP_ARG%" (
    for %%F in ("%BACKUP_ARG%") do set "BACKUP_FILE=%%~fF"
) else if exist "%PROJECT_ROOT%\%BACKUP_ARG%" (
    for %%F in ("%PROJECT_ROOT%\%BACKUP_ARG%") do set "BACKUP_FILE=%%~fF"
) else if exist "%PROJECT_ROOT%\database\backups\%BACKUP_ARG%" (
    for %%F in ("%PROJECT_ROOT%\database\backups\%BACKUP_ARG%") do set "BACKUP_FILE=%%~fF"
) else (
    echo [ERROR] Backup file not found: "%BACKUP_ARG%"
    exit /b 1
)

for %%F in ("!BACKUP_FILE!") do set "FILE_SIZE=%%~zF"
if "!FILE_SIZE!"=="" set "FILE_SIZE=0"
if !FILE_SIZE! leq 0 (
    echo [ERROR] Backup file is empty: "!BACKUP_FILE!"
    exit /b 1
)

rem --- 2. Check interactive / non-interactive flags ---
set "NON_INTERACTIVE=0"
if /i "%~2"=="--yes" set "NON_INTERACTIVE=1"
if /i "%~2"=="--non-interactive" set "NON_INTERACTIVE=1"
if /i "%~2"=="-y" set "NON_INTERACTIVE=1"
if /i "%~3"=="--yes" set "NON_INTERACTIVE=1"
if /i "%~3"=="--non-interactive" set "NON_INTERACTIVE=1"
if /i "%~3"=="-y" set "NON_INTERACTIVE=1"

rem --- 3. Load configuration from environment or .env ---
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
    echo [ERROR] DB_NAME is not configured.
    exit /b 1
)
if "%DB_USER%"=="" (
    echo [ERROR] DB_USER is not configured.
    exit /b 1
)

rem --- 4. Locate mysql client executable ---
set "MYSQL_EXE="
if not "%MYSQL_BIN%"=="" (
    set "CLEAN_BIN=%MYSQL_BIN:"=%"
    if exist "!CLEAN_BIN!\mysql.exe" (
        set "MYSQL_EXE=!CLEAN_BIN!\mysql.exe"
    )
)
if "%MYSQL_EXE%"=="" (
    for %%X in (mysql.exe) do (
        set "MYSQL_EXE=%%~$PATH:X"
    )
)
if "%MYSQL_EXE%"=="" (
    echo [ERROR] mysql.exe was not found in MYSQL_BIN or system PATH.
    echo Please verify MYSQL_BIN in .env or add MySQL bin directory to PATH.
    exit /b 1
)

echo ===================================================================
echo Database Restore Confirmation
echo Target Database : %DB_NAME%
echo Host            : %DB_HOST%:%DB_PORT%
echo User            : %DB_USER%
echo Source File     : !BACKUP_FILE!
echo File Size       : !FILE_SIZE! bytes
echo ===================================================================

rem --- 5. Confirmation prompt (interactive mode only) ---
if "%NON_INTERACTIVE%"=="0" (
    echo WARNING: Restoring will overwrite all existing data in database '%DB_NAME%'!
    echo To proceed, type 'RESTORE' exactly:
    set /p "USER_CONFIRM=Enter confirmation: "
    if not "!USER_CONFIRM!"=="RESTORE" (
        echo [ABORTED] Restore cancelled by user. Confirmation mismatch.
        exit /b 1
    )
)

rem --- 6. Pre-restore safety backup ---
echo Creating pre-restore safety backup...
call "%SCRIPT_DIR%backup.bat"
if !ERRORLEVEL! neq 0 (
    echo [ERROR] Pre-restore safety backup failed.
    echo Aborting restore operation to protect current database.
    exit /b 1
)
echo Pre-restore safety backup created successfully.

rem --- 7. Execute restore via mysql client ---
echo Executing restore into database '%DB_NAME%'...
set "MYSQL_PWD=%DB_PASSWORD%"
type "!BACKUP_FILE!" | "%MYSQL_EXE%" --default-character-set=utf8mb4 --host=%DB_HOST% --port=%DB_PORT% --user=%DB_USER% "%DB_NAME%"
set "RESTORE_EXIT=!ERRORLEVEL!"
set "MYSQL_PWD="

rem --- 8. Verify exit code and report result ---
if !RESTORE_EXIT! neq 0 (
    echo [ERROR] Database restore failed with exit code !RESTORE_EXIT!.
    echo The restore may have applied partially. Check the pre-restore backup in database\backups\ to recover.
    exit /b !RESTORE_EXIT!
)

echo [SUCCESS] Database '%DB_NAME%' successfully restored from '!BACKUP_FILE!'.
exit /b 0
