@echo off
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
IF %ERRORLEVEL% NEQ 0 (
    echo Warning: Git push failed. Check Git output or try manual pull/push.
    pause
) ELSE (
    echo Git push successful.
)

SET "FOUND_ICS=false"
FOR %%F IN ("%PROJECT_PATH%\*.ics") DO (
    start "" "%%~F"
    SET "FOUND_ICS=true"
    goto :found_ics_done
)

:found_ics_done
IF "%FOUND_ICS%"=="false" (
    echo Warning: No .ics file found after script execution.
)

pause