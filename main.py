"""
Unreal Engine INI Visual Merger & Hub
Main Application Entry Point (Python 3.13+ Compatible)
Includes:
 - Windows OS Dark/Light mode registry auto-detection
 - Native Windows 10/11 DWM titlebar styling
 - Custom MP3 / Audio Player (load your own MP3, WAV, or MID, with retro synth fallback)
 - Advanced Developer Mode toggle (collapsible CLI monitor & Manual INI Direct Editor)
 - Custom App & Window Icon handling
"""
import sys
import os
import threading
import webbrowser
import traceback


def write_startup_error(exc_type, exc_value, exc_traceback):
    """Persist startup failures because windowed builds have no console."""
    details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    log_locations = [
        os.path.join(os.path.dirname(os.path.realpath(sys.executable)), "UnrealIniMerger_startup.log"),
        os.path.join(os.environ.get("TEMP", os.getcwd()), "UnrealIniMerger_startup.log")
    ]
    for log_path in dict.fromkeys(log_locations):
        try:
            with open(log_path, "a", encoding="utf-8") as log_file:
                log_file.write(details + "\n")
            break
        except OSError:
            continue


sys.excepthook = write_startup_error

# =========================================================================
# Python 3.13+ Environment & Tkinter Diagnostic Check
# =========================================================================
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ImportError as e:
    print("=" * 70)
    print(" [ERROR] Tkinter is not found in your Python installation!")
    print("=" * 70)
    print("Python on Windows requires the 'tcl/tk and IDLE' optional feature.")
    print("\nHOW TO FIX IN 30 SECONDS:")
    print("1. Open Windows Settings -> 'Installed apps' (or run Python installer).")
    print("2. Click on 'Python 3.13', then click 'Modify'.")
    print("3. Check the box for 'tcl/tk and IDLE' and finish the installer.")
    print("4. Re-run 'python main.py'.")
    print("=" * 70)
    input("\nPress Enter to exit...")
    sys.exit(1)

from config import (
    SafeRedirectStream,
    configure_styles,
    ensure_app_icon,
    load_app_photo_image,
    THEMES,
    WindowsMciAudioPlayer,
    detect_windows_dark_mode,
    apply_native_titlebar_theme
)
from gui_hub import ProjectHubFrame
from gui_merger import IniMergerFrame
from gui_manual_ini import ManualIniEditorFrame


class UnrealIniProjectMerger(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Unreal INI - Visual Config Merger & Project Hub")
        self.geometry("1420x920")
        self.minsize(1080, 760)

        # Set custom window icon (ICO + PhotoImage)
        icon_path = ensure_app_icon()
        if icon_path and os.path.exists(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass
        
        photo_img = load_app_photo_image()
        if photo_img:
            try:
                self.iconphoto(True, photo_img)
                self._app_icon_ref = photo_img  # Keep reference
            except Exception:
                pass

        # Selected project directories
        self.base_project_dir = tk.StringVar()
        self.source_project_dir = tk.StringVar()

        # Theme system: defaults to 'system' (Windows OS Light/Dark auto-detection)
        self.selected_theme_setting = "system"
        self.current_theme_key = self.resolve_theme_key("system")

        # Audio Player setup (Native Windows MCI for MP3/WAV/MID + Chiptune Fallback)
        self.audio_player = WindowsMciAudioPlayer(self)
        self.music_playing = False
        self.current_track_name = tk.StringVar(value="KERS - MassaHex (Synthwave)")

        # Check for local MP3 file in project folder (e.g. music.mp3, bgm.mp3)
        self.auto_detect_local_mp3()

        # State flags
        self.advanced_mode = tk.BooleanVar(value=False)

        # Apply native Windows DWM Title Bar Theme & Ttk Styles
        self.apply_theme_to_window(self.current_theme_key)

        # Top App Toolbar (Title, Theme Switcher, Audio Player, About Credits, Advanced Dev Mode toggle)
        self.build_top_appbar()

        # Create main content area
        self.content_container = tk.Frame(self, bg=self.get_theme_config()["bg"])
        self.content_container.pack(fill=tk.BOTH, expand=True)

        # Embedded Console Log Monitor (Collapsible - Dev Mode only)
        self.setup_console_monitor()
        sys.excepthook = self.handle_uncaught_exception
        threading.excepthook = self.handle_thread_exception

        # Show landing / hub page initially
        self.show_landing_page()

    def resolve_theme_key(self, setting_key):
        if setting_key == "system":
            return "unreal_dark" if detect_windows_dark_mode() else "classic_clam"
        return setting_key if setting_key in THEMES else "classic_clam"

    def get_theme_config(self):
        return THEMES.get(self.current_theme_key, THEMES["classic_clam"])

    def apply_theme_to_window(self, theme_key):
        cfg = THEMES.get(theme_key, THEMES["classic_clam"])
        configure_styles(theme_key)
        self.configure(bg=cfg["bg"])
        apply_native_titlebar_theme(self, cfg.get("dwm_dark", False), cfg.get("dwm_titlebar_color"))

    def auto_detect_local_mp3(self):
        runtime_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
        # For packaged apps, the audio file is normally beside the executable.
        # sys.argv[0] is also needed when running through a launcher/runtime.
        executable_dir = os.path.dirname(os.path.realpath(sys.executable))
        launcher_dir = os.path.dirname(os.path.realpath(sys.argv[0]))
        search_dirs = [
            runtime_dir,
            os.path.join(runtime_dir, "assets"),
            executable_dir,
            os.path.join(executable_dir, "assets"),
            launcher_dir,
            os.path.join(launcher_dir, "assets"),
            os.getcwd(),
            os.path.join(os.getcwd(), "assets"),
            os.path.dirname(os.path.abspath(__file__)),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
        ]
        search_dirs = list(dict.fromkeys(search_dirs))
        candidates = ["kers.mp3", "KERS.mp3", "music.mp3", "bgm.mp3", "soundtrack.mp3", "theme.mp3", "music.wav"]
        audio_extensions = (".mp3", ".wav", ".mid", ".midi")
        print("[audio] Searching for local audio files...")
        print("[audio] Search directories:", search_dirs)

        def load_audio():
            for s_dir in search_dirs:
                if not os.path.exists(s_dir):
                    print("[audio] Missing directory:", s_dir)
                    continue
                try:
                    files = os.listdir(s_dir)
                except OSError as exc:
                    print(f"[audio] Could not list {s_dir}: {exc}")
                    continue
                print(f"[audio] Files in {s_dir}:", files)
                files_by_lower_name = {name.lower(): name for name in files}
                matching_files = [
                    files_by_lower_name[name.lower()]
                    for name in candidates
                    if name.lower() in files_by_lower_name
                ]
                # Accept renamed/custom tracks as well as the conventional names.
                matching_files.extend(
                    name for name in files
                    if name.lower().endswith(audio_extensions)
                    and name not in matching_files
                )
                for c in matching_files:
                    full_p = os.path.abspath(os.path.join(s_dir, c))
                    print("[audio] Trying:", full_p)
                    if not os.path.isfile(full_p):
                        print("[audio] Not a file:", full_p)
                        continue
                    loaded = self.audio_player.load_file(full_p)
                    print(
                        f"[audio] load_file({full_p!r}) -> {loaded}; "
                        f"has_loaded_file={getattr(self.audio_player, 'has_loaded_file', '<missing>')}"
                    )
                    if loaded:
                        def audio_loaded(name=os.path.basename(full_p)):
                            print(
                                f"[audio] UI callback: has_loaded_file="
                                f"{getattr(self.audio_player, 'has_loaded_file', '<missing>')}, "
                                f"music_playing={self.music_playing}, "
                                f"button_ready={hasattr(self, 'btn_music') and self.btn_music.winfo_exists()}"
                            )
                            self.current_track_name.set(name)
                            # Loading succeeds before the toolbar is built.  Do not
                            # report the track as unavailable merely because the
                            # button is not available yet; toggle_music() will
                            # start playback when the user presses it.
                            if hasattr(self, "btn_music") and self.btn_music.winfo_exists():
                                if self.music_playing:
                                    print("[audio] Autoplay requested after load")
                                    if not self.audio_player.play():
                                        print("[audio] Autoplay failed")
                                        self.music_playing = False
                                        self.current_track_name.set("KERS unavailable")
                                        self.btn_music.config(text="🎵 KERS unavailable", bg="#34495e", fg="#ecf0f1")
                                    else:
                                        self.btn_music.config(text="🔊 KERS (Playing)", bg="#27ae60", fg="#ffffff")
                                else:
                                    theme = self.get_theme_config()
                                    self.btn_music.config(text="🎵 KERS", bg=theme["btn_bg"], fg=theme["btn_fg"])

                            # Keep the successful load state visible to the
                            # controls even when loading completed during startup.
                            if not self.music_playing:
                                theme = self.get_theme_config()
                                if hasattr(self, "btn_music") and self.btn_music.winfo_exists():
                                    self.btn_music.config(text="🎵 KERS", bg=theme["btn_bg"], fg=theme["btn_fg"])

                        self.after(0, audio_loaded)
                        return
            print("[audio] No playable audio file found")
            self.after(0, lambda: self.current_track_name.set("KERS unavailable"))

        # MCI device handles are thread-affine on some Windows audio drivers.
        # Load on the Tk thread so later play/pause commands use the same thread.
        load_audio()

    def build_top_appbar(self):
        t = self.get_theme_config()
        self.top_bar = tk.Frame(self, bg=t["top_bg"], padx=10, pady=5)
        self.top_bar.pack(fill=tk.X, side=tk.TOP)

        self.lbl_title = tk.Label(
            self.top_bar,
            text="UNREAL INI",
            font=("Segoe UI", 10, "bold"),
            fg=t["top_fg"],
            bg=t["top_bg"]
        )
        self.lbl_title.pack(side=tk.LEFT, padx=5)

        # Right Audio, Theme & Dev Mode Controls
        self.right_controls = tk.Frame(self.top_bar, bg=t["top_bg"])
        self.right_controls.pack(side=tk.RIGHT)

        # Theme Selector Dropdown Menu
        theme_frame = tk.Frame(self.right_controls, bg=t["top_bg"])
        theme_frame.pack(side=tk.LEFT, padx=4)

        tk.Label(
            theme_frame,
            text="🎨 Theme:",
            font=("Segoe UI", 8, "bold"),
            fg="#94a3b8",
            bg=t["top_bg"]
        ).pack(side=tk.LEFT, padx=(0, 3))

        self.theme_menu_btn = tk.Menubutton(
            theme_frame,
            text=t["badge"],
            font=("Segoe UI", 8, "bold"),
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            relief="raised",
            padx=6,
            pady=2
        )
        self.theme_menu = tk.Menu(self.theme_menu_btn, tearoff=0)
        self.theme_menu.add_command(label="💻 Windows System Auto", command=lambda: self.change_theme("system"))
        self.theme_menu.add_separator()
        self.theme_menu.add_command(label="🪟 Classic Clam", command=lambda: self.change_theme("classic_clam"))
        self.theme_menu.add_command(label="🌑 Unreal Editor Dark", command=lambda: self.change_theme("unreal_dark"))
        self.theme_menu.add_command(label="🌆 MassaHex Synthwave", command=lambda: self.change_theme("synthwave"))
        self.theme_menu.add_command(label="☀️ Studio Clean Light", command=lambda: self.change_theme("modern_light"))
        self.theme_menu_btn["menu"] = self.theme_menu
        self.theme_menu_btn.pack(side=tk.LEFT)

        # Music Player Frame (Discrete single soundtrack toggle)
        music_frame = tk.Frame(self.right_controls, bg=t["top_bg"])
        music_frame.pack(side=tk.LEFT, padx=4)

        self.btn_music = tk.Button(
            music_frame,
            text="🎵 KERS",
            font=("Segoe UI", 8, "bold"),
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            relief="raised",
            padx=8,
            pady=2,
            command=self.toggle_music
        )
        self.btn_music.pack(side=tk.LEFT, padx=2)

        # About & Credits Button
        self.btn_credits = tk.Button(
            self.right_controls,
            text="ℹ️ Credits",
            font=("Segoe UI", 8, "bold"),
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            relief="raised",
            padx=6,
            pady=2,
            command=self.show_about_credits
        )
        self.btn_credits.pack(side=tk.LEFT, padx=3)

        # Advanced Mode Toggle Button (Reveals bottom CLI & Manual INI tab)
        self.btn_advanced = tk.Button(
            self.right_controls,
            text="🛠️ Advanced Dev Mode: OFF",
            font=("Segoe UI", 8, "bold"),
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            relief="raised",
            padx=8,
            pady=2,
            command=self.toggle_advanced_mode
        )
        self.btn_advanced.pack(side=tk.LEFT, padx=4)

    def change_theme(self, theme_key):
        self.selected_theme_setting = theme_key
        self.current_theme_key = self.resolve_theme_key(theme_key)
        t = self.get_theme_config()
        self.apply_theme_to_window(self.current_theme_key)

        # Update Top bar
        self.top_bar.config(bg=t["top_bg"])
        self.lbl_title.config(bg=t["top_bg"], fg=t["top_fg"])
        self.right_controls.config(bg=t["top_bg"])
        badge_text = "💻 System (" + t["badge"] + ")" if theme_key == "system" else t["badge"]
        self.theme_menu_btn.config(text=badge_text, bg=t["btn_bg"], fg=t["btn_fg"])
        if not self.music_playing:
            self.btn_music.config(bg=t["btn_bg"], fg=t["btn_fg"])
        self.btn_credits.config(bg=t["btn_bg"], fg=t["btn_fg"])
        if not self.advanced_mode.get():
            self.btn_advanced.config(bg=t["btn_bg"], fg=t["btn_fg"])

        # Update content container
        self.content_container.config(bg=t["bg"])

        # Update console frame if created
        if hasattr(self, 'console_text'):
            self.console_text.config(bg=t["console_bg"], fg=t["console_fg"])

        # Refresh currently active view
        if hasattr(self, 'hub_frame') and self.hub_frame.winfo_exists():
            self.show_landing_page()
        elif hasattr(self, 'merger_frame') and self.merger_frame.winfo_exists():
            self.show_merger_page()
        elif hasattr(self, 'manual_ini_frame') and self.manual_ini_frame.winfo_exists():
            base_text = self.manual_ini_frame.txt_base.get("1.0", tk.END)
            source_text = self.manual_ini_frame.txt_source.get("1.0", tk.END)
            self.show_manual_ini_page(
                base_text=base_text,
                source_text=source_text,
                file_label=self.manual_ini_frame.file_label
            )

    def toggle_music(self):
        print(
            f"[audio] toggle_music: current={self.music_playing}, "
            f"has_loaded_file={getattr(self.audio_player, 'has_loaded_file', '<missing>')}"
        )
        self.music_playing = not self.music_playing
        if self.music_playing:
            if not self.audio_player.has_loaded_file:
                print("[audio] Toggle requested before the file was marked loaded")
                self.btn_music.config(text="⏳ Loading KERS...", bg="#34495e", fg="#ecf0f1")
                return

            self.btn_music.config(text="🔊 KERS (Playing)", bg="#27ae60", fg="#ffffff")
            audio_started = self.audio_player.play()
            print(f"[audio] play() -> {audio_started}")
            if not audio_started:
                # MCI can report the file as loaded before its open command has
                # finished processing.  Give it one retry before reporting a
                # genuine playback failure.
                self.btn_music.config(text="⏳ Starting KERS...", bg="#34495e", fg="#ecf0f1")

                def retry_play():
                    if not self.music_playing:
                        return
                    retry_started = self.audio_player.play()
                    print(f"[audio] retry play() -> {retry_started}")
                    if retry_started:
                        self.btn_music.config(text="🔊 KERS (Playing)", bg="#27ae60", fg="#ffffff")
                    else:
                        self.music_playing = False
                        self.current_track_name.set("KERS unavailable")
                        self.btn_music.config(text="🎵 KERS unavailable", bg="#34495e", fg="#ecf0f1")

                self.after(250, retry_play)
            
            # Show friendly notification toast for KERS by MassaHex
            if hasattr(self, 'hub_frame') and self.hub_frame.winfo_exists():
                self.hub_frame.show_friendly_banner(
                    "🎵 Now Playing: 'KERS' by MassaHex (Synthwave)",
                    is_info=True
                )
        else:
            self.btn_music.config(text="🎵 KERS", bg="#34495e", fg="#ecf0f1")
            paused = self.audio_player.pause()
            print(f"[audio] pause() -> {paused}")

    def show_about_credits(self):
        credits_win = tk.Toplevel(self)
        self.credits_win = credits_win
        credits_win.title("About & Credits")
        credits_win.geometry("520x360")
        credits_win.resizable(False, False)
        t = self.get_theme_config()
        credits_win.configure(bg=t["bg"])
        credits_win.update_idletasks()
        apply_native_titlebar_theme(
            credits_win,
            t.get("dwm_dark", False),
            t.get("dwm_titlebar_color")
        )
        credits_win.grab_set()

        # Header
        tk.Label(
            credits_win,
            text="Unreal INI",
            font=("Segoe UI", 12, "bold"),
            fg=t["accent"],
            bg=t["bg"]
        ).pack(pady=(15, 2))

        credit_line = tk.Frame(credits_win, bg=t["bg"])
        credit_line.pack(pady=(0, 10))
        tk.Label(
            credit_line,
            text="♥",
            font=("Segoe UI", 11, "bold"),
            fg="#e53935",
            bg=t["bg"]
        ).pack(side=tk.LEFT, padx=(0, 4))
        tk.Label(
            credit_line,
            text="Built with love by Gemini, GitHub Copilot & MassaHex",
            font=("Segoe UI", 10, "bold"),
            fg=t["fg"],
            bg=t["bg"]
        ).pack(side=tk.LEFT)

        # Soundtrack card
        s_frame = tk.Frame(credits_win, bg=t["card_bg"], padx=15, pady=12, highlightthickness=1, highlightbackground=t["accent"])
        s_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(
            s_frame,
            text="🎵 Official Soundtrack: 'KERS' by MassaHex",
            font=("Segoe UI", 10, "bold"),
            fg=t["accent"],
            bg=t["card_bg"]
        ).pack(anchor="w")

        tk.Label(
            s_frame,
            text="Genre: Synthwave (Non-Copyright / Royalty Free)\nListen, support, and add to your playlist on SoundCloud:",
            font=("Segoe UI", 9),
            fg=t["fg"],
            bg=t["card_bg"],
            justify="left"
        ).pack(anchor="w", pady=(4, 8))

        btn_sc = tk.Button(
            s_frame,
            text="🔗 Open SoundCloud (soundcloud.com/massahex/kers)",
            font=("Segoe UI", 9, "bold"),
            bg="#f97316",
            fg="#ffffff",
            relief="raised",
            padx=10,
            pady=4,
            command=lambda: webbrowser.open("https://soundcloud.com/massahex/kers")
        )
        btn_sc.pack(anchor="w")

        # Close button
        tk.Button(
            credits_win,
            text="Close",
            font=("Segoe UI", 9, "bold"),
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            padx=15,
            pady=4,
            command=credits_win.destroy
        ).pack(pady=(15, 0))

        credits_win.protocol("WM_DELETE_WINDOW", credits_win.destroy)

    def toggle_advanced_mode(self):
        is_adv = not self.advanced_mode.get()
        self.advanced_mode.set(is_adv)

        if is_adv:
            self.btn_advanced.config(text="🛠️ Advanced Dev Mode: ON", bg="#e67e22", fg="#ffffff")
            self.console_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 10))
        else:
            self.btn_advanced.config(text="🛠️ Advanced Dev Mode: OFF", bg="#34495e", fg="#ecf0f1")
            self.console_frame.pack_forget()

        if hasattr(self, 'hub_frame') and self.hub_frame.winfo_exists():
            self.hub_frame.on_advanced_mode_changed(is_adv)

    def setup_console_monitor(self):
        self.console_frame = ttk.LabelFrame(
            self,
            text=" 💻 CLI Output & Runtime Error Monitor (Advanced Dev Mode) ",
            padding=5
        )

        sub_frame = ttk.Frame(self.console_frame)
        sub_frame.pack(fill=tk.BOTH, expand=True)

        self.console_text = tk.Text(
            sub_frame,
            height=4,
            bg="#1e1e1e",
            fg="#dcdcdc",
            font=("Consolas", 9),
            state=tk.DISABLED,
            wrap=tk.WORD
        )
        scrollbar = ttk.Scrollbar(sub_frame, orient="vertical", command=self.console_text.yview)
        self.console_text.configure(yscrollcommand=scrollbar.set)

        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        sys.stdout = SafeRedirectStream(sys.stdout, self.console_text, self.show_error_popup)
        sys.stderr = SafeRedirectStream(sys.stderr, self.console_text, self.show_error_popup)

    def show_error_popup(self, title, details):
        if not self.winfo_exists():
            return
        error_win = tk.Toplevel(self)
        t = self.get_theme_config()
        error_win.title(title)
        error_win.geometry("720x430")
        error_win.configure(bg=t["bg"])
        error_win.transient(self)

        tk.Label(
            error_win,
            text="An error occurred. Copy the details below and send them to the developer.",
            bg=t["bg"],
            fg=t["fg"],
            font=("Segoe UI", 10, "bold"),
            wraplength=680,
            justify="left"
        ).pack(anchor="w", padx=14, pady=(14, 8))

        details_box = tk.Text(
            error_win,
            wrap=tk.WORD,
            bg=t["console_bg"],
            fg=t["console_fg"],
            insertbackground=t["console_fg"],
            font=("Consolas", 9),
            relief="flat"
        )
        details_box.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)
        details_box.insert("1.0", details)
        details_box.configure(state=tk.DISABLED)

        button_bar = tk.Frame(error_win, bg=t["bg"])
        button_bar.pack(fill=tk.X, padx=14, pady=(4, 14))

        def copy_details():
            self.clipboard_clear()
            self.clipboard_append(details)
            self.update()

        tk.Button(button_bar, text="Copy Error Details", command=copy_details, bg=t["btn_bg"], fg=t["btn_fg"]).pack(side=tk.LEFT)
        tk.Button(button_bar, text="Close", command=error_win.destroy, bg=t["btn_bg"], fg=t["btn_fg"]).pack(side=tk.RIGHT)
        error_win.grab_set()

    def handle_uncaught_exception(self, exc_type, exc_value, exc_traceback):
        import traceback
        details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.show_error_popup("Application Error", details)

    def handle_thread_exception(self, args):
        import traceback
        details = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
        self.after(0, lambda: self.show_error_popup("Background Task Error", details))

    def clear_content_area(self):
        for widget in self.content_container.winfo_children():
            widget.destroy()

    def show_landing_page(self):
        self.clear_content_area()
        self.hub_frame = ProjectHubFrame(
            parent=self.content_container,
            app=self,
            base_dir_var=self.base_project_dir,
            source_dir_var=self.source_project_dir,
            on_launch_merger=self.show_merger_page,
            on_open_manual_ini=self.show_manual_ini_page
        )
        self.hub_frame.pack(fill=tk.BOTH, expand=True)

    def show_merger_page(self):
        self.clear_content_area()
        self.merger_frame = IniMergerFrame(
            parent=self.content_container,
            app=self,
            base_dir=self.base_project_dir.get(),
            source_dir=self.source_project_dir.get(),
            on_back_to_hub=self.show_landing_page
        )
        self.merger_frame.pack(fill=tk.BOTH, expand=True)

    def show_manual_ini_page(self, base_text="", source_text="", file_label="Direct INI"):
        self.clear_content_area()
        self.manual_ini_frame = ManualIniEditorFrame(
            parent=self.content_container,
            app=self,
            initial_base_text=base_text,
            initial_source_text=source_text,
            file_label=file_label,
            on_back_to_hub=self.show_landing_page
        )
        self.manual_ini_frame.pack(fill=tk.BOTH, expand=True)

    def destroy(self):
        self.audio_player.stop()
        super().destroy()


if __name__ == "__main__":
    try:
        app = UnrealIniProjectMerger()
        app.mainloop()
    except BaseException:
        write_startup_error(*sys.exc_info())
        raise
