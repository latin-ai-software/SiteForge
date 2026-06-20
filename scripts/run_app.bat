@echo off
REM Set UTF-8 encoding for Python on Windows
set PYTHONIOENCODING=utf-8

REM Run the main application
python app.py %*

pause
