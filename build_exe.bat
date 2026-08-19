@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"
title Building Unreal INI Visual Merger Standalone Single-File EXE (Python 3.13+)
echo =========================================================================
echo  Unreal Engine INI Visual Merger - 100%% Standalone EXE Builder
echo  (Creates a single, self-contained UnrealIniMerger.exe with Custom Icon)
echo =========================================================================
echo.

:: Detect Python executable (Try py launcher first, then python in PATH)
set "PY_CMD="
py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
  set "PY_CMD=py -3"
  ) else (
  python --version >nul 2>&1
  if %errorlevel% equ 0 (
    set "PY_CMD=python"
  )
)

if "%PY_CMD%"=="" (
  echo [ERROR] No Python interpreter found in PATH!
  echo Please install Python 3.13 from https://www.python.org/downloads/
  echo NOTE: Ensure you check "Add python.exe to PATH" during installation.
  pause
  exit /b 1
)

echo [*] Detected Python environment:
%PY_CMD% --version

echo.
echo [*] Checking for a running UnrealIniMerger instance...
tasklist /FI "IMAGENAME eq UnrealIniMerger.exe" /NH | findstr /I /B /C:"UnrealIniMerger.exe" >nul
if %errorlevel% equ 0 (
  echo.
  echo [ERROR] UnrealIniMerger.exe is currently running and locked.
  echo Please close every running UnrealIniMerger window, then run this build again.
  pause
  exit /b 1
)

echo.
echo [*] Step 1: Upgrading pip and installing PyInstaller + Pillow...
%PY_CMD% -m pip install --upgrade pip
%PY_CMD% -m pip install -r requirements.txt

echo.
echo [*] Step 2: Testing Tkinter availability...
%PY_CMD% -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
  echo.
  echo =====================================================================
  echo [WARNING] Tkinter is missing from your Python installation!
  echo =====================================================================
  echo Fix in 30 seconds:
  echo 1. Open Windows Settings -> Installed Apps -> Python 3.13 -> Modify
  echo 2. Make sure the checkbox for "tcl/tk and IDLE" is CHECKED.
  echo 3. Complete the setup and re-run build_exe.bat.
  echo =====================================================================
  echo.
  pause
  exit /b 1
)

echo.
echo [*] Step 3: Generating custom app icon if missing...
%PY_CMD% -c "from config import ensure_app_icon; ensure_app_icon()" >nul 2>&1

set "ICON_ARG="
if exist "app_icon.ico" (
  set "ICON_ARG=--icon app_icon.ico --add-data app_icon.ico;."
  echo [*] Attached custom app icon: app_icon.ico
)

set "AUDIO_ARG="
if exist "kers.mp3" (
  set "AUDIO_ARG=--add-data kers.mp3;."
  echo [*] Bundling soundtrack: kers.mp3
  ) else if exist "assets\kers.mp3" (
  set "AUDIO_ARG=--add-data assets\kers.mp3;."
  echo [*] Bundling soundtrack: assets\kers.mp3
  ) else if exist "music.mp3" (
  set "AUDIO_ARG=--add-data music.mp3;."
  echo [*] Bundling soundtrack: music.mp3
  ) else if exist "assets\music.mp3" (
  set "AUDIO_ARG=--add-data assets\music.mp3;."
  echo [*] Bundling soundtrack: assets\music.mp3
)

echo.
echo [*] Step 4: Compiling into a SINGLE standalone .EXE file (Final Polish)...
%PY_CMD% -m PyInstaller --noconfirm --clean --onefile --windowed --noupx --name "UnrealIniMerger" --version-file version_info.txt %ICON_ARG% %AUDIO_ARG% --hidden-import PIL._imagingtk --hidden-import PIL._tkinter_finder --exclude-module PIL.AvifImagePlugin --exclude-module tkinter.test --exclude-module matplotlib --exclude-module scipy --exclude-module numpy --exclude-module pytest --exclude-module unittest --exclude-module pydoc --exclude-module distutils --exclude-module setuptools main.py

if %errorlevel% equ 0 (
  echo.
  echo =====================================================================
  echo  [SUCCESS] 100%% STANDALONE BUILD COMPLETE!
  echo.
  echo  Your standalone single executable is ready at:
  echo  dist\UnrealIniMerger.exe
  echo.
  echo  You can copy and move 'UnrealIniMerger.exe' anywhere!
  echo  It has its custom icon and does NOT need Python or loose files.
  echo =====================================================================
  echo.
  ) else (
  echo.
  echo [ERROR] PyInstaller compilation failed. Check log output above.
)

pause
