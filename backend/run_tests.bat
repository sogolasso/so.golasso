@echo off
echo Running Só Golasso Tests...
echo.

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Run the tests
python run_tests.py

REM Keep the window open if there are errors
if errorlevel 1 pause

REM Deactivate virtual environment
if exist "venv\Scripts\deactivate.bat" (
    call venv\Scripts\deactivate.bat
) 