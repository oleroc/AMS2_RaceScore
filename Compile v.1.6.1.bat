REM RaceScore 1.6.1: builds with Python 3.12 (PyQt5, aiohttp, PyInstaller 6.10), not the default python
REM Initialize log file
set "LOGFILE=build_exe.log"
echo. > "%LOGFILE%"

REM Function to log messages (both to console and file)
call :log "====================================================="
call :log "Building RaceManger Executable"
call :log "====================================================="
call :log ""

REM Change to the script directory
cd /d "%~dp0"




if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"

"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" Convert_base64.py
"%LOCALAPPDATA%\Programs\Python\Python312\python.exe" -m PyInstaller RaceMonitor_v1.6.1.spec

REM Check if build was successful
if errorlevel 1 (
    call :log ""
    call :log "====================================================="
    call :log "BUILD FAILED!"
    call :log "====================================================="
    call :log "Check the output above for errors."
    call :log ""
    pause
    exit /b 1
) else (
    call :log ""
    call :log "====================================================="
    call :log "BUILD SUCCESSFUL!"
    call :log "====================================================="
    call :log ""
    call :log "Executable location: dist\AMS2 RaceMonitor_v1.6.1.exe"
    call :log ""
    
    REM Check if executable exists
    if exist "dist\AMS2 RaceMonitor_v1.6.1.exe" (
        call :log "File size:"
        for %%I in ("dist\AMS2 RaceMonitor_v1.6.1.exe") do call :log "  %%~zI bytes"
        call :log ""
        
        REM Copy executable to script directory, overwriting old version
        call :log "Copying executable to script directory..."
        if exist "AMS2 RaceMonitor_v1.6.1.exe" (
            call :log "Overwriting existing AMS2 RaceMonitor_v1.6.1.exe..."
            del "AMS2 RaceMonitor_v1.6.1.exe" 2>nul
        )
        
        copy "dist\AMS2 RaceMonitor_v1.6.1.exe" "AMS2 RaceMonitor_v1.6.1.exe" >nul
        if errorlevel 1 (
            call :log "Warning: Failed to copy executable to script directory!"
        ) else (
            call :log "Successfully copied AMS2 RaceMonitor_v1.6.1.exe to script directory."
            call :log ""
            call :log "New executable location: AMS2 RaceMonitor_v1.6.1.exe"
        )
        call :log ""
        
        call :log "You can also find the executable in the 'dist\' folder."
        call :log ""
    ) else (
        call :log "Warning: Executable was not found in expected location!"
    )
)



if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
call :log ""
call :log "Build log saved to: %LOGFILE%"
Rem pause
goto :eof
REM Function to log messages to both console and file
:log
echo %~1
echo %~1 >> "%LOGFILE%"
goto :eof