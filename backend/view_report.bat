@echo off
echo Attempting to run test report viewer...

REM Create test-reports directory if it doesn't exist
if not exist "test-reports" mkdir test-reports

REM Try Python from common installation paths
SET PYTHON_PATHS=^
C:\Python39\python.exe;^
C:\Python310\python.exe;^
C:\Python311\python.exe;^
C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\python.exe;^
C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python310\python.exe;^
C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python311\python.exe;^
%LOCALAPPDATA%\Programs\Python\Python39\python.exe;^
%LOCALAPPDATA%\Programs\Python\Python310\python.exe;^
%LOCALAPPDATA%\Programs\Python\Python311\python.exe

REM First try to generate the report
for %%p in (%PYTHON_PATHS%) do (
    if exist "%%p" (
        echo Found Python at: %%p
        echo Generating test report...
        "%%p" run_tests.py
        if exist "test-reports\test_report.html" (
            echo Test report generated successfully.
            start "" "test-reports\test_report.html"
            goto :end
        )
    )
)

echo Python was not found in common locations.
echo Please ensure Python is installed and try one of these options:
echo 1. Install Python from python.org
echo 2. Add Python to your system PATH
echo 3. Run 'py run_tests.py' if you have the Python launcher
echo.
echo Unable to generate or open the test report.
echo Press any key to exit...
pause > nul

:end 