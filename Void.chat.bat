@echo off
REM Change directory to the folder where this .bat file is located
cd /d "%~dp0"

echo Starting VoidChat Backend...
REM Run the application using standard python
python src\app.py

REM If the app crashes or is closed, keep the window open so you can read the error
pause