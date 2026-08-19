"""
Unreal Engine Project Discovery & Metadata Scanner
Includes aspect-ratio preserving thumbnail loader (no image distortion).
"""
import os
import glob
from config import PIL_AVAILABLE

if PIL_AVAILABLE:
    from PIL import Image, ImageTk, ImageOps


def get_epic_launcher_project_paths():
    """Finds Unreal project roots from standard folders and Epic Launcher config."""
    paths = [
        os.path.expanduser("~/Documents/Unreal Projects"),
        "C:/Unreal Projects",
        "D:/Unreal Projects",
        "E:/Unreal Projects"
    ]
    
    launcher_ini = os.path.expandvars(r"%LOCALAPPDATA%\EpicGamesLauncher\Saved\Config\Windows\GameUserSettings.ini")
    if os.path.exists(launcher_ini):
        try:
            with open(launcher_ini, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if line.strip().startswith("CreatedProjectPaths="):
                        p = line.split("=", 1)[1].strip().strip('"')
                        p = os.path.normpath(p)
                        if os.path.isdir(p) and p not in paths:
                            paths.append(p)
        except Exception:
            pass
    return paths


def scan_unreal_projects(root_dirs):
    """
    Recursively scans specified root directories for .uproject files,
    extracting project titles, uproject paths, and auto-screenshot thumbnails.
    """
    uproject_files = []
    for r_dir in root_dirs:
        if os.path.isdir(r_dir):
            uproject_files.extend(glob.glob(os.path.join(r_dir, "*", "*.uproject")))
            uproject_files.extend(glob.glob(os.path.join(r_dir, "*.uproject")))

    discovered_projects = []
    for uproj_path in sorted(list(set(uproject_files))):
        proj_dir = os.path.normpath(os.path.dirname(uproj_path))
        proj_name = os.path.basename(uproj_path).replace(".uproject", "")
        
        screenshot_path = os.path.join(proj_dir, "Saved", "AutoScreenshot.png")
        if not os.path.exists(screenshot_path):
            screenshot_path = os.path.join(proj_dir, "Content", "Thumbnail.png")
        if not os.path.exists(screenshot_path):
            screenshot_path = None

        # Game icon in root folder (e.g. icon.png, Icon.png)
        icon_path = os.path.join(proj_dir, "icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(proj_dir, "Icon.png")
        if not os.path.exists(icon_path):
            icon_path = os.path.join(proj_dir, "Resources", "Icon128.png")
        if not os.path.exists(icon_path):
            icon_path = None

        discovered_projects.append({
            "name": proj_name,
            "path": proj_dir,
            "uproject": uproj_path,
            "screenshot": screenshot_path,
            "icon": icon_path
        })

    return discovered_projects


def load_project_thumbnail(screenshot_path, canvas_size=(230, 130)):
    """
    Loads project screenshot and fits it into canvas_size preserving exact aspect ratio.
    Pads with clean dark letterbox so wide/tall images are never stretched or distorted.
    """
    if not screenshot_path or not PIL_AVAILABLE:
        return None
    try:
        img = Image.open(screenshot_path)
        img = img.convert("RGBA")
        img.thumbnail(canvas_size, Image.Resampling.LANCZOS)
        
        bg = Image.new("RGBA", canvas_size, (15, 23, 42, 255))
        offset = ((canvas_size[0] - img.width) // 2, (canvas_size[1] - img.height) // 2)
        bg.paste(img, offset, mask=img if img.mode == 'RGBA' else None)

        return ImageTk.PhotoImage(bg)
    except Exception:
        return None


def load_project_icon(icon_path, icon_size=(24, 24)):
    """
    Loads game root icon (icon.png) with high-quality resampling for project cards.
    """
    if not icon_path or not PIL_AVAILABLE:
        return None
    try:
        img = Image.open(icon_path)
        img = img.convert("RGBA")
        img.thumbnail(icon_size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None
