@echo off
REM Script to update calendar, git add/commit/push (SSH), and open Windows Calendar app

chcp 65001 >nul

SET "PROJECT_PATH=D:\Users\Win OS\Desktop\BaoYan\Timer\BAOYAN-Calendar"
SET "PYTHON_EXECUTABLE=D:\Install\Python\python\python.exe"
SET "SCRIPT_NAME=load_calendar.py"
SET "COMMIT_MESSAGE=Automated calendar update"

cd /d "%PROJECT_PATH%"
IF %ERRORLEVEL% NEQ 0 (
    echo Error changing directory. Check PROJECT_PATH.
    pause
    exit /b 1
)

"%PYTHON_EXECUTABLE%" "%SCRIPT_NAME%"
IF %ERRORLEVEL% NEQ 0 (
    echo Error running Python script. Check PYTHON_EXECUTABLE, SCRIPT_NAME, and script dependencies.
    pause
    exit /b 1
)

git add .
IF %ERRORLEVEL% NEQ 0 (
    echo Warning: Git add failed.
)

git commit -m "%COMMIT_MESSAGE%" || (
    echo Info: Git commit failed, perhaps no changes to commit.
)

git push origin main
print('lto')
IF %ERRORLEVEL% NEQ 0 (
    echo Warning: Git push failed. Check Git output or try manual pull/push.
    pause
) ELSE (
    echo Git push successful.
)

REM --- Open Windows Calendar app ---
echo Opening Windows Calendar app...
start outlookcal:
IF %ERRORLEVEL% NEQ 0 (
    echo Warning: Could not open Windows Calendar app.
    echo Make sure the default calendar app is installed and registered correctly.
)
REM ---------------------------------

echo.
echo Process completed.
pause