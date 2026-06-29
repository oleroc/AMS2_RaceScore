@echo off
echo Starting AMS2 API Simulation Environment for Testmode
echo ====================================================
echo This will create simulated API data files for testing 
echo the enhanced multi-race monitoring system.
echo.
echo To use testmode:
echo 1. Set testmode = True in config.ini
echo 2. Run RaceMonitor_v1.7.0.py
echo 3. The system will use simulated data instead of real AMS2
echo.
echo Starting API simulator...
python api_simulator.py
pause
