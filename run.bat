@echo off
setlocal
py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    py -3 main.py
) else (
    python main.py
)
if %errorlevel% neq 0 (
    echo.
    echo [INFO] If the window closed unexpectedly, review the output above.
    pause
)
