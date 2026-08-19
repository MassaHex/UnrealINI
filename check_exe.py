# check_exe.py
import sys
import os
from PyInstaller.archive.readers import CArchiveReader

# Replace with your actual EXE name
exe_path = "dist/UnrealIniMerger.exe"

if not os.path.exists(exe_path):
    print(f"Error: {exe_path} not found. Run your build script first.")
    sys.exit(1)

print(f"--- Contents of {exe_path} ---")
try:
    archive = CArchiveReader(exe_path)
    # Print header
    print(f"{'Size (bytes)':<15} {'Name'}")
    print("-" * 40)
    
    total_size = 0
    mp3_count = 0
    
    for name, (pos, length, ulength, flag, typecode) in archive.toc.items():
        print(f"{length:<15} {name}")
        total_size += length
        if name.lower().endswith(".mp3"):
            mp3_count += 1
            
    print("-" * 40)
    print(f"Total Uncompressed Size: {total_size / 1024 / 1024:.2f} MB")
    print(f"MP3 Files Found: {mp3_count}")
    
    if mp3_count > 1:
        print("\n[WARNING] Multiple MP3 files detected! This is likely causing the extra size.")
        
except Exception as e:
    print(f"Error reading archive: {e}")
    print("Note: If the EXE is UPX compressed, this script might fail. Try Method 1 (7-Zip).")   