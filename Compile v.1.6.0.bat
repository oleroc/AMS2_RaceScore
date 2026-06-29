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

python Convert_base64.py
pyinstaller RaceMonitor_v1.6.0.spec

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
    call :log "Executable location: dist\BFF Repacker\BFF Repacker.exe"
    call :log ""
    
    REM Check if executable exists
    if exist "dist\AMS2 RaceMonitor_v1.6.0.exe" (
        call :log "File size:"
        for %%I in ("dist\AMS2 RaceMonitor_v1.6.0.exe") do call :log "  %%~zI bytes"
        call :log ""
        
        REM Copy executable to script directory, overwriting old version
        call :log "Copying executable to script directory..."
        if exist "AMS2 RaceMonitor_v1.6.0.exe" (
            call :log "Overwriting existingAMS2 RaceMonitor_v1.6.0.exe..."
            del "AMS2 RaceMonitor_v1.6.0.exe" 2>nul
        )
        
        copy "dist\AMS2 RaceMonitor_v1.6.0.exe" "AMS2 RaceMonitor_v1.6.0.exe" >nul
        if errorlevel 1 (
            call :log "Warning: Failed to copy executable to script directory!"
        ) else (
            call :log "Successfully copied BFF Repacker.exe to script directory."
            call :log ""
            call :log "New executable location: AMS2 RaceMonitor_v1.6.0.exe"
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