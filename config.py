"""
Configuration, Multi-Theme System, Native Windows MCI Audio Player, Multi-Size ICO Generator & Safe Stream Interceptor
"""
import io
import sys
import os
import ctypes
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

# Check for Pillow support (graceful fallback if not present)
try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def resource_path(filename):
    """Resolve a bundled resource or a source-tree resource path."""
    bundled_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(bundled_dir, filename),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), filename),
        os.path.abspath(filename),
    ]
    for candidate in candidates:
        if os.path.isfile(candidate):
            return candidate
    return candidates[0]


THEMES = {
    "classic_clam": {
        "id": "classic_clam",
        "name": "Classic Tkinter (Clam)",
        "badge": "🪟 Clam",
        "bg": "#f0f0f0",
        "fg": "#2c3e50",
        "top_bg": "#2c3e50",
        "top_fg": "#ffffff",
        "btn_bg": "#34495e",
        "btn_fg": "#ecf0f1",
        "card_bg": "#ffffff",
        "card_border": "#bdc3c7",
        "base_card": "#ebf5fb",
        "source_card": "#e8f8f5",
        "base_border": "#2471a3",
        "source_border": "#229954",
        "accent": "#2471a3",
        "console_bg": "#1e1e1e",
        "console_fg": "#dcdcdc",
        "status_bg": "#e0e0e0",
        "status_fg": "#555555",
        "dwm_dark": False,
        "dwm_titlebar_color": 0x503e2c  # BGR for #2c3e50
    },
    "unreal_dark": {
        "id": "unreal_dark",
        "name": "Unreal Editor Dark",
        "badge": "🌑 UE Dark",
        "bg": "#181a1f",
        "fg": "#e2e8f0",
        "top_bg": "#121316",
        "top_fg": "#ffffff",
        "btn_bg": "#282c34", 
        "btn_fg": "#e2e8f0",
        "card_bg": "#21242b",
        "card_border": "#2f333d",
        "base_card": "#14233c",
        "source_card": "#112a22",
        "base_border": "#0070e0",
        "source_border": "#10b981",
        "accent": "#0070e0",
        "console_bg": "#0f1014",
        "console_fg": "#38bdf8",
        "status_bg": "#14161a",
        "status_fg": "#94a3b8",
        "dwm_dark": True,
        "dwm_titlebar_color": 0x161312  # BGR for #121316
    },
    "synthwave": {
        "id": "synthwave",
        "name": "MassaHex Synthwave",
        "badge": "🌆 Synthwave",
        "bg": "#160d26",
        "fg": "#fdf2f8",
        "top_bg": "#2a0845",
        "top_fg": "#ffffff",
        "btn_bg": "#2c174d",
        "btn_fg": "#fce7f3",
        "card_bg": "#22133b",
        "card_border": "#5a2282",
        "base_card": "#2b1050",
        "source_card": "#3b0b3e",
        "base_border": "#00f0ff",
        "source_border": "#ff2a85",
        "accent": "#ff2a85",
        "console_bg": "#120a1f",
        "console_fg": "#ff2a85",
        "status_bg": "#120a1f",
        "status_fg": "#d8b4fe",
        "dwm_dark": True,
        "dwm_titlebar_color": 0x45082a  # BGR for #2a0845
    },
    "modern_light": {
        "id": "modern_light",
        "name": "Studio Clean Light",
        "badge": "☀️ Light",
        "bg": "#f8fafc",
        "fg": "#0f172a",
        "top_bg": "#0f172a",
        "top_fg": "#ffffff",
        "btn_bg": "#ffffff",
        "btn_fg": "#0f172a",
        "card_bg": "#ffffff",
        "card_border": "#cbd5e1",
        "base_card": "#eff6ff",
        "source_card": "#ecfdf5",
        "base_border": "#3b82f6",
        "source_border": "#10b981",
        "accent": "#3b82f6",
        "console_bg": "#1e293b",
        "console_fg": "#f8fafc",
        "status_bg": "#e2e8f0",
        "status_fg": "#475569",
        "dwm_dark": False,
        "dwm_titlebar_color": 0x2a170f  # BGR for #0f172a
    }
}


def detect_windows_dark_mode():
    """
    Detects Windows 10/11 system-wide light/dark mode preference via registry key:
    HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize\AppsUseLightTheme
    """
    if sys.platform != "win32":
        return True
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SoftwareMicrosoftWindowsCurrentVersionThemesPersonalize")
        val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return val == 0
    except Exception:
        return True


def apply_native_titlebar_theme(root_window, is_dark=True, titlebar_color_bgr=None):
    """
    Applies immersive dark mode and optional custom color to the native Windows OS titlebar (Win 10/11) using DWM API.
    """
    if sys.platform != "win32":
        return
    try:
        root_window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(root_window.winfo_id())
        if not hwnd:
            hwnd = root_window.winfo_id()
        
        # DWMWA_USE_IMMERSIVE_DARK_MODE (20 on Win 10 20H1+ and Win 11, 19 on older Win 10)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19
        DWMWA_CAPTION_COLOR = 35 # Windows 11 custom title bar color
        
        val = ctypes.c_int(1 if is_dark else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(val), ctypes.sizeof(val))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_OLD, ctypes.byref(val), ctypes.sizeof(val))
        
        if titlebar_color_bgr is not None:
            c_val = ctypes.c_int(titlebar_color_bgr)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_CAPTION_COLOR, ctypes.byref(c_val), ctypes.sizeof(c_val))
    except Exception:
        pass


def configure_styles(theme_key="classic_clam"):
    """Applies theme colors to Tkinter ttk styles."""
    theme = THEMES.get(theme_key, THEMES["classic_clam"])
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(".", background=theme["bg"], foreground=theme["fg"], fieldbackground=theme["card_bg"])
    style.configure("TFrame", background=theme["bg"])
    style.configure("TLabel", background=theme["bg"], foreground=theme["fg"], font=("Segoe UI", 10))
    style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=5)
    style.configure("Header.TLabel", background=theme["bg"], font=("Segoe UI", 12, "bold"), foreground=theme["fg"])
    style.configure("TLabelframe", background=theme["bg"], bordercolor=theme["card_border"])
    style.configure("TLabelframe.Label", background=theme["bg"], font=("Segoe UI", 10, "bold"), foreground=theme["fg"])
    style.configure("Treeview", background=theme["card_bg"], foreground=theme["fg"], fieldbackground=theme["card_bg"])
    style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
    style.configure("TButton", background=theme["btn_bg"], foreground=theme["btn_fg"], font=("Segoe UI", 9, "bold"), padding=5)
    style.map("TButton",
        background=[('active', theme["accent"]), ('pressed', theme["accent"])],
        foreground=[('active', theme["top_fg"]), ('pressed', theme["top_fg"])]
    )
    # Configure TScrollbar for all themes
    style.configure("Vertical.TScrollbar", 
                    background=theme["card_border"], 
                    troughcolor=theme["bg"], 
                    bordercolor=theme["card_border"], 
                    arrowcolor=theme["fg"])
    style.configure("Horizontal.TScrollbar", 
                    background=theme["card_border"], 
                    troughcolor=theme["bg"], 
                    bordercolor=theme["card_border"], 
                    arrowcolor=theme["fg"])
    
    style.map("Vertical.TScrollbar",
              background=[('active', theme["accent"]), ('pressed', theme["accent"])])
    style.map("Horizontal.TScrollbar",
              background=[('active', theme["accent"]), ('pressed', theme["accent"])])


def bind_mousewheel(widget, canvas):
    """
    Recursively binds mouse wheel event to canvas scrolling for all nested child widgets on Windows.
    """
    def _on_mousewheel(event):
        try:
            if canvas.winfo_exists():
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        except Exception:
            pass

    widget.bind("<MouseWheel>", _on_mousewheel, add="+")
    for child in widget.winfo_children():
        bind_mousewheel(child, canvas)


def ensure_app_icon():
    """
    Generates multi-size .ico icon file (256, 128, 64, 48, 32, 16) from assets/UnrealINI.png
    or creates programmatically if PNG is not present.
    """
    icon_filename = resource_path("app_icon.ico")
    if os.path.exists(icon_filename) and os.path.getsize(icon_filename) > 500:
        return icon_filename

    if not PIL_AVAILABLE:
        return None

    # Check for uploaded 256x256 PNG asset
    candidates = [
        resource_path(os.path.join("assets", "UnrealINI.png")),
        resource_path("UnrealINI.png"),
        os.path.join(os.path.dirname(__file__), "assets", "UnrealINI.png"),
        os.path.join(os.path.dirname(__file__), "UnrealINI.png")
    ]
    png_source = None
    for p in candidates:
        if os.path.exists(p) and os.path.isfile(p):
            png_source = p
            break

    try:
        if png_source:
            img = Image.open(png_source).convert("RGBA")
        else:
            # Generate vector emblem programmatically
            img = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rounded_rectangle((8, 8, 248, 248), radius=56, fill="#0f172a", outline="#3b82f6", width=8)
            draw.rounded_rectangle((20, 20, 236, 236), radius=44, outline="#1d4ed8", width=4)
            # Left & Right 'i' dots
            draw.ellipse((56, 44, 80, 68), fill="#38bdf8")
            draw.ellipse((176, 44, 200, 68), fill="#38bdf8")
            # U-Bridge
            draw.line([(68, 88), (68, 160)], fill="#38bdf8", width=16)
            draw.arc((68, 120, 188, 200), start=0, end=180, fill="#38bdf8", width=16)
            draw.line([(188, 88), (188, 160)], fill="#38bdf8", width=16)
            # Central 'n'
            draw.line([(108, 112), (108, 152)], fill="#67e8f9", width=12)
            draw.arc((108, 92, 148, 132), start=180, end=0, fill="#67e8f9", width=12)
            draw.line([(148, 112), (148, 152)], fill="#67e8f9", width=12)

        # Save multi-resolution Windows ICO (256 down to 16 for high-DPI taskbar and titlebars)
        ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
        img.save(icon_filename, format="ICO", sizes=ico_sizes)
        
        # Also mirror into assets folder if it exists
        if os.path.exists("assets") and os.path.isdir("assets"):
            try:
                img.save("assets/app_icon.ico", format="ICO", sizes=ico_sizes)
            except Exception:
                pass

        return icon_filename
    except Exception:
        return None


def load_app_photo_image():
    """Returns a PhotoImage for window iconphoto."""
    if not PIL_AVAILABLE:
        return None
    candidates = [
        resource_path("app_icon.ico"),
        resource_path(os.path.join("assets", "UnrealINI.png")),
        resource_path("UnrealINI.png"),
        os.path.join(os.path.dirname(__file__), "assets", "UnrealINI.png"),
        os.path.join(os.path.dirname(__file__), "UnrealINI.png")
    ]
    for p in candidates:
        if os.path.exists(p) and os.path.isfile(p):
            try:
                img = Image.open(p).convert("RGBA").resize((32, 32), Image.Resampling.LANCZOS)
                return ImageTk.PhotoImage(img)
            except Exception:
                pass
    return None


class WindowsMciAudioPlayer:
    """
    Native Windows Media Control Interface (MCI) Audio Player with Overlap Tail-Layering.
    Seamlessly loops at 0:40:42 by triggering the next voice while letting the old voice ring out its full tail.
    """
    def __init__(self, ui_root=None):
        instance_id = f"{id(self):x}"
        self.alias_a = f"unreal_bgm_a_{instance_id}"
        self.alias_b = f"unreal_bgm_b_{instance_id}"
        self.current_alias = self.alias_a
        self.current_file = None
        self.has_loaded_file = False
        self.last_error_code = 0
        self.is_playing = False
        self.loop_duration_ms = 0
        self._loop_thread = None
        self._loop_job = None
        self._ui_root = ui_root
        self._stop_loop = threading.Event()
        self._mci_lock = threading.RLock()

    def _mci_send(self, cmd):
        with self._mci_lock:
            try:
                buf = ctypes.create_unicode_buffer(256)
                self.last_error_code = ctypes.windll.winmm.mciSendStringW(cmd, buf, 255, 0)
                return buf.value
            except Exception:
                self.last_error_code = -1
                return ""

    def _mci_error_text(self):
        if not self.last_error_code:
            return ""
        buf = ctypes.create_unicode_buffer(256)
        try:
            if ctypes.windll.winmm.mciGetErrorStringW(self.last_error_code, buf, 255):
                return buf.value
        except Exception:
            pass
        return "unknown MCI error"

    def load_file(self, file_path):
        with self._mci_lock:
            self.has_loaded_file = False
            resolved = file_path
            if not os.path.exists(resolved):
                if hasattr(sys, "_MEIPASS"):
                    meipass_path = os.path.join(sys._MEIPASS, os.path.basename(file_path))
                    if os.path.exists(meipass_path):
                        resolved = meipass_path

                if not os.path.exists(resolved):
                    return False

            self._stop_loop.set()
            self.is_playing = False
            if self._loop_job is not None and self._ui_root is not None:
                self._ui_root.after_cancel(self._loop_job)
                self._loop_job = None
            norm_path = os.path.abspath(resolved).replace("\\", "/")

            # Close any previous audio streams before opening both aliases.
            self._mci_send(f'close {self.alias_a}')
            self._mci_send(f'close {self.alias_b}')

            # Open dual audio instances for overlap tail layering.
            self._mci_send(f'open "{norm_path}" type mpegvideo alias {self.alias_a}')
            if self.last_error_code != 0:
                self._mci_send(f'open "{norm_path}" alias {self.alias_a}')
                if self.last_error_code != 0:
                    return False
            self._mci_send(f'set {self.alias_a} time format milliseconds')
            if self.last_error_code != 0:
                self._mci_send(f'close {self.alias_a}')
                return False
            self._mci_send(f'open "{norm_path}" type mpegvideo alias {self.alias_b}')
            if self.last_error_code != 0:
                self._mci_send(f'open "{norm_path}" alias {self.alias_b}')
                if self.last_error_code != 0:
                    self._mci_send(f'close {self.alias_a}')
                    return False
            self._mci_send(f'set {self.alias_b} time format milliseconds')
            if self.last_error_code != 0:
                self._mci_send(f'close {self.alias_a}')
                self._mci_send(f'close {self.alias_b}')
                return False

            self.current_file = resolved
            self.current_alias = self.alias_a
            duration_text = self._mci_send(f'status {self.alias_a} length')
            try:
                duration_ms = int(duration_text)
                if duration_ms > 0:
                    self.loop_duration_ms = duration_ms
            except (TypeError, ValueError):
                pass
            self._stop_loop.clear()
            self.has_loaded_file = True
            return True

    def _loop_monitor(self):
        while not self._stop_loop.is_set() and self.is_playing:
            pos_str = self._mci_send(f'status {self.current_alias} position')
            try:
                pos = int(pos_str)
                if pos >= max(0, self.loop_duration_ms - 100):
                    # Switch to the other voice and start from 0
                    next_alias = self.alias_b if self.current_alias == self.alias_a else self.alias_a
                    old_alias = self.current_alias

                    # Start next voice immediately
                    self._mci_send(f'seek {next_alias} to start')
                    self._mci_send(f'play {next_alias} from 0')
                    self.current_alias = next_alias

                    # Let the old voice ring out its reverb/delay tail, then rewind after 5 seconds
                    def _cleanup_old_voice(alias):
                        time.sleep(5.0)
                        if not self._stop_loop.is_set():
                            self._mci_send(f'stop {alias}')
                            self._mci_send(f'seek {alias} to start')

                    threading.Thread(target=_cleanup_old_voice, args=(old_alias,), daemon=True).start()
            except Exception:
                pass
            time.sleep(0.03)

    def _loop_tick(self):
        if self._stop_loop.is_set() or not self.is_playing or not self.has_loaded_file:
            self._loop_job = None
            return

        pos_str = self._mci_send(f'status {self.current_alias} position')
        try:
            pos = int(pos_str)
            if pos >= max(0, self.loop_duration_ms - 100):
                next_alias = self.alias_b if self.current_alias == self.alias_a else self.alias_a
                old_alias = self.current_alias
                self._mci_send(f'seek {next_alias} to start')
                self._mci_send(f'play {next_alias} from 0')
                if self.last_error_code == 0:
                    self.current_alias = next_alias
                    self._ui_root.after(5000, self._cleanup_old_voice, old_alias)
        except (TypeError, ValueError):
            pass

        self._loop_job = self._ui_root.after(30, self._loop_tick)

    def _cleanup_old_voice(self, alias):
        if not self._stop_loop.is_set() and self.has_loaded_file:
            self._mci_send(f'stop {alias}')
            self._mci_send(f'seek {alias} to start')

    def play(self):
        if self.has_loaded_file:
            # Explicitly restart the selected instance so retries do not inherit
            # a paused or completed position from an earlier command.
            self._mci_send(f'seek {self.current_alias} to start')
            self._mci_send(f'play {self.current_alias} from 0')
            if self.last_error_code != 0:
                print(
                    f"[audio] MCI play failed: code={self.last_error_code}, "
                    f"message={self._mci_error_text()}"
                )
                self.has_loaded_file = False
                self.is_playing = False
                return False
            self.is_playing = True
            self._stop_loop.clear()
            if self._ui_root is not None:
                self._loop_job = self._ui_root.after(30, self._loop_tick)
            else:
                self._loop_thread = threading.Thread(target=self._loop_monitor, daemon=True)
                self._loop_thread.start()
            return True
        return False

    def pause(self):
        if self.has_loaded_file:
            self._stop_loop.set()
            if self._loop_job is not None and self._ui_root is not None:
                self._ui_root.after_cancel(self._loop_job)
                self._loop_job = None
            self._mci_send(f'pause {self.alias_a}')
            self._mci_send(f'pause {self.alias_b}')
            self.is_playing = False

    def stop(self):
        if self.has_loaded_file:
            self._stop_loop.set()
            if self._loop_job is not None and self._ui_root is not None:
                self._ui_root.after_cancel(self._loop_job)
                self._loop_job = None
            self._mci_send(f'stop {self.alias_a}')
            self._mci_send(f'seek {self.alias_a} to start')
            self._mci_send(f'stop {self.alias_b}')
            self._mci_send(f'seek {self.alias_b} to start')
            self._mci_send(f'close {self.alias_a}')
            self._mci_send(f'close {self.alias_b}')
            self.has_loaded_file = False
            self.current_alias = self.alias_a
            self.is_playing = False


class RetroChiptuneSynth:
    """
    Background 8-bit tracker / keygen chiptune synthesizer (Code-X / Warez style).
    Used as built-in fallback when no custom MP3 is loaded.
    """
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.notes = [
            440, 523, 659, 880, 659, 523, 440, 523,
            392, 493, 587, 783, 587, 493, 392, 493,
            349, 440, 523, 698, 523, 440, 349, 440,
            329, 415, 493, 659, 493, 415, 329, 415,
            880, 1046, 1318, 1760, 1318, 1046, 880, 1046,
            783, 987, 1174, 1567, 1174, 987, 783, 987,
            698, 880, 1046, 1396, 1046, 880, 698, 880,
            659, 830, 987, 1318, 987, 830, 659, 830
        ]

    def _loop(self):
        try:
            import winsound
            idx = 0
            while self.is_running:
                freq = self.notes[idx % len(self.notes)]
                idx += 1
                winsound.Beep(freq, 110)
                time.sleep(0.015)
        except Exception:
            pass

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.is_running = False


class SafeRedirectStream(io.TextIOBase):
    """
    Python 3.13 compliant TextIOBase stream interceptor.
    Uses properties for encoding/errors to avoid AttributeError in CPython _TextIOBase.
    """
    def __init__(self, original_stream, console_widget, error_callback=None):
        super().__init__()
        self.original_stream = original_stream
        self.console_widget = console_widget
        self.error_callback = error_callback
        self._traceback_text = ""
        self._encoding = getattr(original_stream, "encoding", None) or "utf-8"
        self._errors = getattr(original_stream, "errors", None) or "replace"

    @property
    def encoding(self):
        return self._encoding

    @property
    def errors(self):
        return self._errors

    def writable(self):
        return True

    def readable(self):
        return False

    def seekable(self):
        return False

    def isatty(self):
        if self.original_stream and hasattr(self.original_stream, "isatty"):
            try:
                return self.original_stream.isatty()
            except Exception:
                pass
        return False

    def write(self, message):
        if message is None:
            return 0
            
        if self.original_stream:
            try:
                self.original_stream.write(message)
            except Exception:
                pass
        
        if message and self.console_widget:
            try:
                if self.console_widget.winfo_exists():
                    self.console_widget.config(state=tk.NORMAL)
                    self.console_widget.insert(tk.END, str(message))
                    self.console_widget.see(tk.END)
                    self.console_widget.config(state=tk.DISABLED)
                    
                    # Tracebacks are written in multiple chunks; wait for the
                    # final exception line before showing the copyable dialog.
                    msg_str = str(message).lower()
                    if self._traceback_text or "traceback" in msg_str:
                        self._traceback_text += str(message)
                        if ":" in msg_str and any(
                            marker in msg_str for marker in ("error", "exception", "failed")
                        ):
                            details = self._traceback_text.strip()
                            if self.error_callback:
                                self.error_callback("Runtime Error", details)
                            else:
                                messagebox.showerror("Runtime Error", details)
                            self._traceback_text = ""
            except Exception:
                pass
        return len(message) if message else 0

    def flush(self):
        if self.original_stream and hasattr(self.original_stream, "flush"):
            try:
                self.original_stream.flush()
            except Exception:
                pass
