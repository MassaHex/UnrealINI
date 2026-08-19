@echo off
setlocal
cd /d "%~dp0"
title Building UnrealIniMerger Debug EXE

echo Building console-enabled diagnostic executable...

set "PY_CMD="
py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
  set "PY_CMD=py -3"
) else (
  python --version >nul 2>&1
  if %errorlevel% equ 0 set "PY_CMD=python"
)

if "%PY_CMD%"=="" (
  echo [ERROR] No Python interpreter found.
  pause
  exit /b 1
)

%PY_CMD% -m PyInstaller --noconfirm --clean --onefile --console --noupx --name "UnrealIniMergerDebug" --version-file version_info.txt --icon app_icon.ico --add-data "app_icon.ico;." --add-data "kers.mp3;." --hidden-import PIL._imagingtk --hidden-import PIL._tkinter_finder --exclude-module PIL.AvifImagePlugin --exclude-module tkinter.test --exclude-module matplotlib --exclude-module scipy --exclude-module numpy --exclude-module pytest --exclude-module unittest --exclude-module pydoc --exclude-module distutils --exclude-module setuptools main.py

if %errorlevel% equ 0 (
  echo.
  echo [SUCCESS] Debug executable created at:
  echo dist\UnrealIniMergerDebug.exe
) else (
  echo.
  echo [ERROR] Debug build failed.
)
pause
