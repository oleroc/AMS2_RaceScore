@echo off
echo Starting Realistic Race Scenario Generator
echo ==========================================
echo This script reads real data from RaceDB.db to create
echo authentic racing scenarios for testing the enhanced
echo multi-race monitoring system.
echo.
echo Features:
echo - Pulls real participant names, tracks, cars, and lap times
echo - Creates 4 concurrent races with max 6 laps each
echo - Uses actual performance data for realistic simulation
echo - Tests participant-based race detection
echo.
echo Make sure RaceDB.db exists in the current directory!
echo.
echo Starting realistic race scenario generator...
python realistic_race_scenarios.py
pause
