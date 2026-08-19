<p align="center">
   <img src="assets/UnrealINI.png" alt="Unreal INI Visual Merger icon" width="160">
</p>

<h1 align="center">Unreal INI Visual Merger</h1>

<p align="center">A visual project hub for comparing, resolving, and merging Unreal Engine INI configuration files.</p>

A native Windows desktop application built with Python & Tkinter for visually comparing, resolving, and merging Unreal Engine `.ini` configuration files (e.g. merging custom gameplay projects with the **Game Animation Sample Project**, Lyra Starter Game, or template updates).

---

## 📁 Modular File Structure

- **`main.py`** : Application entry point and Tkinter window coordinator.
- **`config.py`** : Styling, Pillow availability, and safe CLI stream redirection.
- **`project_scanner.py`** : Epic Games Launcher detection, project root searching, and thumbnail extraction.
- **`ini_engine.py`** : Unreal Engine INI section & key parser, diff engine, and merge compiler.
- **`gui_hub.py`** : Project Hub landing page with **double-selection safeguard**, non-intrusive status banner, and swap controls.
- **`gui_merger.py`** : Visual INI comparator with granular Left / Right / Skip controls, bulk resolution, and overwrite buttons.
- **`requirements.txt`** : Dependencies (Pillow for thumbnail previews, PyInstaller for standalone .exe export).
- **`build_exe.bat`** : 1-click Windows batch script to compile into `dist/UnrealIniMerger.exe`.
- **`run.bat`** : 1-click batch launcher to run with python.

---

## 🚀 How to Run

1. Make sure Python 3.9+ is installed.
2. Install optional requirements (for thumbnails):
   ```bash
   pip install -r requirements.txt
   ```
3. Launch the application:
   ```bash
   python main.py
   ```
   *(Or double-click `run.bat`)*

---

## 📦 How to Build Standalone Windows .EXE (100% Single File)

Double-click **`build_exe.bat`** or run:
```bash
pip install -r requirements.txt
pyinstaller --noconfirm --clean --onefile --windowed --noupx --name "UnrealIniMerger" --collect-all tkinter main.py
```

Your single-file standalone executable will be generated at:
```
dist/UnrealIniMerger.exe
```

You can copy and move **`UnrealIniMerger.exe`** to any folder or any Windows PC. It is completely standalone and **does NOT need Python, scripts, or any other files to run**.

### Sending the EXE to another PC

Windows may block an unsigned PyInstaller executable downloaded from Discord. If a security warning appears, save the file, open its **Properties**, select **Unblock** if shown, and choose **Apply**. Verify that the file was not changed during transfer with:

```powershell
Get-FileHash .\UnrealIniMerger.exe -Algorithm SHA256
```

Compare that hash with the sender's hash. Do not disable antivirus protection to run the file. If Defender quarantines it, submit the build as a false positive or distribute a code-signed executable.

---

## ❤️ Credits & Soundtrack

- **Project Architect & Creator**: **MassaHex**
- **AI Engineering**: **GitHub Copilot**
- **Official Soundtrack**: **"KERS" by MassaHex** (Synthwave, Non-Copyright / Royalty Free)
  - 🔗 **Listen on SoundCloud**: [https://soundcloud.com/massahex/kers](https://soundcloud.com/massahex/kers)
  - *Feel free to support, stream, and add "KERS" to your playlists!*
