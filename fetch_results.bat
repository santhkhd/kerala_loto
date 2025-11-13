@echo off
echo Fetching latest Kerala lottery results...
echo.
python updateloto.py
echo.
echo Generating history file...
node generate-history.js
echo.
echo Results fetched and history updated.
pause