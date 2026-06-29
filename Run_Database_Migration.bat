@echo off
echo.
echo ========================================
echo AMS2 RaceScore Database Migration v1.7.0
echo ========================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7 or later
    pause
    exit /b 1
)

:: Check if migration script exists
if not exist "migrate_to_v1_7_0.py" (
    echo ERROR: Migration script not found
    echo Please ensure migrate_to_v1_7_0.py is in the same directory
    pause
    exit /b 1
)

:: Check if database exists
if not exist "RaceDB.db" (
    echo No database found - nothing to migrate
    echo The application will create a new v1.7.0 database when started
    pause
    exit /b 0
)

echo Found database: RaceDB.db
echo.

:: Run migration
echo Starting migration process...
echo.
python migrate_to_v1_7_0.py RaceDB.db

if errorlevel 1 (
    echo.
    echo Migration failed! Check migration.log for details
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo Migration completed successfully!
    echo ========================================
    echo.
    echo Your database has been upgraded to v1.7.0
    echo You can now start AMS2 RaceScore normally
    echo.
    echo Backup created: RaceDB.db.backup_[timestamp]
    echo Migration log: migration.log
    echo.
)

pause
