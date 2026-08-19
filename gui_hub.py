"""
Project Hub & Selection Landing Page
Features:
 - Aspect-ratio preserved project cards (no image stretching)
 - Seamless mouse wheel scrolling on Windows
 - Non-Disruptive Double-Selection Safeguard
 - Advanced Mode (reveals Manual INI Direct Editor)
"""
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import bind_mousewheel
from project_scanner import (
    get_epic_launcher_project_paths,
    scan_unreal_projects,
    load_project_thumbnail,
    load_project_icon
)


class ProjectHubFrame(tk.Frame):
    def __init__(self, parent, app, base_dir_var, source_dir_var, on_launch_merger, on_open_manual_ini):
        self.app = app
        t = self.app.get_theme_config()
        
        super().__init__(parent, bg=t["bg"], padx=20, pady=15)
        self.app = app
        self.base_dir_var = base_dir_var
        self.source_dir_var = source_dir_var
        self.on_launch_merger = on_launch_merger
        self.on_open_manual_ini = on_open_manual_ini

        self.selection_mode = "base"
        self.toast_after_id = None
        self.blink_job = None
        self.blink_state = False

        self.thumbnail_images = {}
        self.icon_images = {}
        self.project_cards = {}
        self.detected_projects = []

        self.build_ui()
        self.after(100, self.auto_scan_projects)

    def build_ui(self, app=None):
        if app is not None:
            self.app = app
        t = self.app.get_theme_config()
        # Action Toolbar Row (No redundant title)
        header_frame = tk.Frame(self, bg=t["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 6))
        

        # Manual INI Direct Editor button (revealed when Advanced Mode is on or standalone)
        self.btn_manual_ini = tk.Button(
            header_frame,
            text="📝 Manual INI Direct Editor",
            font=("Segoe UI", 9, "bold"),
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            relief="raised",
            padx=8,
            pady=3,
            command=self.on_open_manual_ini
        )
        if self.app.advanced_mode.get():
            self.btn_manual_ini.pack(side=tk.RIGHT, padx=4)

        # In-Window Notification Banner
        self.lbl_toast_banner = tk.Label(
            self,
            text="",
            font=("Segoe UI", 10, "bold"),
            bg=t["card_bg"],
            fg=t["fg"],
            padx=12,
            pady=7,
            highlightthickness=1,
            highlightbackground=t["accent"],
            anchor="w"
        )

        # Wizard Step Control Bar
        wizard_control_frame = tk.Frame(
            self,
            bg=t["card_bg"],
            padx=10,
            pady=8,
            highlightbackground=t["card_border"],
            highlightthickness=1
        )
        wizard_control_frame.pack(fill=tk.X, pady=(0, 10))

        self.lbl_wizard_instruction = tk.Label(
            wizard_control_frame,
            text="",
            font=("Segoe UI", 11, "bold"),
            bg=t["card_bg"],
            fg=t["fg"]
        )
        self.lbl_wizard_instruction.pack(side=tk.LEFT, padx=5)

        wiz_btn_frame = tk.Frame(wizard_control_frame, bg=t["card_bg"])
        wiz_btn_frame.pack(side=tk.RIGHT)

        self.btn_select_base_tab = tk.Button(
            wiz_btn_frame,
            text="1. Select Base Project",
            font=("Segoe UI", 9, "bold"),
            relief="raised",
            padx=8,
            pady=4,
            command=lambda: self.switch_wizard_mode("base")
        )
        self.btn_select_base_tab.pack(side=tk.LEFT, padx=4)

        self.btn_select_source_tab = tk.Button(
            wiz_btn_frame,
            text="2. Select Source Project",
            font=("Segoe UI", 9, "bold"),
            relief="raised",
            padx=8,
            pady=4,
            command=lambda: self.switch_wizard_mode("source")
        )
        self.btn_select_source_tab.pack(side=tk.LEFT, padx=4)

        # Selection Status Overview Card
        status_frame = ttk.LabelFrame(self, text=" Wizard Selection Overview ", padding=10)
        status_frame.pack(fill=tk.X, pady=(0, 10))

        sel_grid = ttk.Frame(status_frame)
        sel_grid.pack(fill=tk.X)

        ttk.Label(sel_grid, text="Base/Target Project:", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, sticky=tk.W, padx=5)
        self.lbl_base_selected = ttk.Label(sel_grid, text="None selected", foreground="#c0392b")
        self.lbl_base_selected.grid(row=0, column=1, sticky=tk.W, padx=5)

        ttk.Label(sel_grid, text="Source/Mod Project:", font=("Segoe UI", 10, "bold")).grid(row=1, column=0, sticky=tk.W, padx=5, pady=4)
        self.lbl_source_selected = ttk.Label(sel_grid, text="None selected", foreground="#c0392b")
        self.lbl_source_selected.grid(row=1, column=1, sticky=tk.W, padx=5, pady=4)

        action_bar = ttk.Frame(status_frame)
        action_bar.pack(fill=tk.X, pady=(8, 0))

        self.btn_launch_merger = tk.Button(
            action_bar,
            text="🚀 Launch Visual INI Merger",
            font=("Segoe UI", 10, "bold"),
            bg=t["btn_bg"],
            fg=t["btn_fg"],
            relief="raised",
            padx=14,
            pady=6,
            command=self.verify_and_launch,
            state=tk.DISABLED
        )
        self.btn_launch_merger.pack(side=tk.RIGHT)

        ttk.Button(action_bar, text="🔄 Reset Selection", command=self.reset_selection).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_bar, text="⇄ Swap Base & Source", command=self.swap_selection).pack(side=tk.LEFT, padx=3)

        # Gallery Header
        gallery_header = tk.Frame(self, bg=t["bg"])
        gallery_header.pack(fill=tk.X, pady=(4, 4))

        tk.Label(
            gallery_header,
            text="Detected Unreal Projects on System",
            font=("Segoe UI", 11, "bold"),
            fg=t["fg"],
            bg=t["bg"]
        ).pack(side=tk.LEFT)

        ttk.Button(gallery_header, text="📁 Scan Custom Directory...", command=self.scan_custom_directory_prompt).pack(side=tk.RIGHT)

        # Scrollable Gallery Container with Mousewheel support
        gallery_container = tk.Frame(self, bg=t["bg"])
        gallery_container.pack(fill=tk.BOTH, expand=True, pady=4)

        self.canvas_gallery = tk.Canvas(gallery_container, highlightthickness=0, bg=t["bg"])
        self.gallery_scroll = ttk.Scrollbar(gallery_container, orient="vertical", command=self.canvas_gallery.yview)

        self.gallery_scrollable = tk.Frame(self.canvas_gallery, bg=t["bg"])
        self.gallery_scrollable.bind("<Configure>", lambda e=None: self.canvas_gallery.configure(scrollregion=self.canvas_gallery.bbox("all")))

        self.canvas_window = self.canvas_gallery.create_window((0, 0), window=self.gallery_scrollable, anchor="nw")
        self.canvas_gallery.bind("<Configure>", lambda e=None: self.canvas_gallery.itemconfig(self.canvas_window, width=e.width))
        self.canvas_gallery.configure(yscrollcommand=self.gallery_scroll.set)

        self.canvas_gallery.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.gallery_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind Mouse Wheel for smooth native scrolling
        bind_mousewheel(self.canvas_gallery, self.canvas_gallery)
        bind_mousewheel(self.gallery_scrollable, self.canvas_gallery)

        self.update_wizard_ui_state()

    def on_advanced_mode_changed(self, is_advanced):
        if is_advanced:
            self.btn_manual_ini.pack(side=tk.RIGHT, padx=4)
        else:
            self.btn_manual_ini.pack_forget()

    def show_friendly_banner(self, message, is_info=True):
        t = self.app.get_theme_config()
        bg_color = t["card_bg"]
        fg_color = t["fg"]
        border_color = t["accent"]

        self.lbl_toast_banner.config(text=message, bg=bg_color, fg=fg_color, highlightbackground=border_color)
        self.lbl_toast_banner.pack(fill=tk.X, pady=(0, 10))

        if self.toast_after_id:
            self.after_cancel(self.toast_after_id)
        self.toast_after_id = self.after(4500, lambda: self.lbl_toast_banner.pack_forget())

    def switch_wizard_mode(self, mode):
        self.selection_mode = mode
        self.update_wizard_ui_state()

    def update_wizard_ui_state(self):
        t = self.app.get_theme_config()
        if self.selection_mode == "base":
            self.lbl_wizard_instruction.config(text="👉 Wizard Step 1: Click on any project card below to set Base (Target).")
            self.btn_select_base_tab.config(bg=t["base_border"], fg="#ffffff", relief="sunken")
            self.btn_select_source_tab.config(bg=t["btn_bg"], fg=t["btn_fg"], relief="raised")
        else:
            self.lbl_wizard_instruction.config(text="👉 Wizard Step 2: Click on any project card below to set Source (Update/Mod).")
            self.btn_select_source_tab.config(bg=t["source_border"], fg="#ffffff", relief="sunken")
            self.btn_select_base_tab.config(bg=t["btn_bg"], fg=t["btn_fg"], relief="raised")

        b_val = self.base_dir_var.get()
        s_val = self.source_dir_var.get()

        if b_val:
            self.lbl_base_selected.config(text=f"{b_val}", foreground=t["base_border"])
        else:
            self.lbl_base_selected.config(text="None selected", foreground="#c0392b")

        if s_val:
            self.lbl_source_selected.config(text=f"{s_val}", foreground=t["source_border"])
        else:
            self.lbl_source_selected.config(text="None selected", foreground="#c0392b")

        # The selections are shared with the merger page, but the launch
        # button state belongs to this frame. Restore it when returning here.
        if b_val and s_val and os.path.normpath(b_val) != os.path.normpath(s_val):
            self.btn_launch_merger.config(state=tk.NORMAL)
            if not self.blink_job:
                self.start_launch_blinking()
        else:
            self.btn_launch_merger.config(state=tk.DISABLED)
            self.stop_launch_blinking()

    def handle_card_selection(self, proj_path, proj_name):
        normalized_path = os.path.normpath(proj_path)
        current_base = self.base_dir_var.get()
        current_source = self.source_dir_var.get()

        if self.selection_mode == "base":
            if normalized_path == current_base:
                self.show_friendly_banner(
                    f"ℹ️ '{proj_name}' is already selected as Base. Choose a different project for Source below.",
                    is_info=True
                )
                self.selection_mode = "source"
                self.update_wizard_ui_state()
                return

            if normalized_path == current_source:
                self.show_friendly_banner(
                    f"ℹ️ '{proj_name}' was your Source project and has been switched to Base. Please pick a new Source project.",
                    is_info=True
                )
                self.source_dir_var.set("")
                self.base_dir_var.set(normalized_path)
                self.selection_mode = "source"
            else:
                self.base_dir_var.set(normalized_path)
                self.show_friendly_banner(f"✓ Base project set to '{proj_name}'. Now select your Source project.", is_info=True)
                self.selection_mode = "source"

        else:  # source mode
            if normalized_path == current_source:
                self.show_friendly_banner(f"ℹ️ '{proj_name}' is already selected as the Source project.", is_info=True)
                return

            if normalized_path == current_base:
                self.show_friendly_banner(
                    f"ℹ️ '{proj_name}' is currently your Base project. Please choose a different project for Source, or click 'Swap'.",
                    is_info=False
                )
                return
            else:
                self.source_dir_var.set(normalized_path)
                self.show_friendly_banner(f"✓ Source project set to '{proj_name}'. Ready to merge!", is_info=True)

        self.update_card_highlights()
        self.update_wizard_ui_state()

        if self.base_dir_var.get() and self.source_dir_var.get():
            self.btn_launch_merger.config(state=tk.NORMAL)
            self.start_launch_blinking()
        else:
            self.stop_launch_blinking()

    def update_card_highlights(self):
        t = self.app.get_theme_config()
        base_path = self.base_dir_var.get()
        source_path = self.source_dir_var.get()

        for p_dir, card in self.project_cards.items():
            norm = os.path.normpath(p_dir)
            if norm == base_path:
                card.config(bg=t["base_card"], highlightbackground=t["base_border"], highlightthickness=2)
                if hasattr(card, 'select_btn'):
                    card.select_btn.config(text="✓ Base Selected")
            elif norm == source_path:
                card.config(bg=t["source_card"], highlightbackground=t["source_border"], highlightthickness=2)
                if hasattr(card, 'select_btn'):
                    card.select_btn.config(text="✓ Source Selected")
            else:
                card.config(bg=t["card_bg"], highlightbackground=t["card_border"], highlightthickness=1)
                if hasattr(card, 'select_btn'):
                    card.select_btn.config(text="Select Project")

    def swap_selection(self):
        b = self.base_dir_var.get()
        s = self.source_dir_var.get()
        if not b and not s:
            self.show_friendly_banner("ℹ️ No projects are selected to swap yet.", is_info=True)
            return
        self.base_dir_var.set(s)
        self.source_dir_var.set(b)
        self.update_card_highlights()
        self.update_wizard_ui_state()
        self.show_friendly_banner("⇄ Base and Source projects have been swapped.", is_info=True)
        if self.base_dir_var.get() and self.source_dir_var.get():
            self.btn_launch_merger.config(state=tk.NORMAL)
            self.start_launch_blinking()
        else:
            self.stop_launch_blinking()

    def reset_selection(self):
        self.base_dir_var.set("")
        self.source_dir_var.set("")
        self.selection_mode = "base"
        self.update_wizard_ui_state()
        self.stop_launch_blinking()
        self.btn_launch_merger.config(state=tk.DISABLED, bg="#e0e0e0", fg="#555555")
        self.update_card_highlights()
        self.show_friendly_banner("🔄 Selections cleared. Select a Base project to start.", is_info=True)

    def start_launch_blinking(self):
        if self.blink_job:
            self.after_cancel(self.blink_job)
        self.blink_state = False
        self.blink_loop()

    def stop_launch_blinking(self):
        if self.blink_job:
            self.after_cancel(self.blink_job)
            self.blink_job = None
        t = self.app.get_theme_config()
        self.btn_launch_merger.config(bg=t["btn_bg"], fg=t["btn_fg"])

    def blink_loop(self):
        if not self.base_dir_var.get() or not self.source_dir_var.get():
            t = self.app.get_theme_config()
            self.btn_launch_merger.config(bg=t["btn_bg"], fg=t["btn_fg"])
            return
        if self.blink_state:
            self.btn_launch_merger.config(bg="#f1c40f", fg="#000000")
        else:
            self.btn_launch_merger.config(bg="#f39c12", fg="#ffffff")
        self.blink_state = not self.blink_state
        self.blink_job = self.after(600, self.blink_loop)

    def auto_scan_projects(self):
        def scan():
            try:
                paths = get_epic_launcher_project_paths()
                valid = [p for p in paths if os.path.isdir(p)]
                projects = scan_unreal_projects(valid) if valid else []
                error = None
            except Exception as exc:
                projects, error = [], exc

            self.after(0, lambda: self._finish_auto_scan(projects, error))

        threading.Thread(target=scan, daemon=True).start()

    def _finish_auto_scan(self, projects, error):
        if not self.winfo_exists():
            return
        if error is not None:
            self.show_empty_gallery(f"Project scan failed: {error}")
            return
        if projects:
            self.populate_gallery(projects)
        else:
            self.show_empty_gallery("No default Unreal project folders discovered. Click 'Scan Custom Directory'.")

    def scan_custom_directory_prompt(self):
        d = filedialog.askdirectory(title="Select Folder Containing Unreal Projects")
        if d:
            new_found = scan_unreal_projects([d])
            if new_found:
                existing_paths = {os.path.normpath(p["path"]).lower() for p in self.detected_projects}
                added_count = 0
                for np in new_found:
                    if os.path.normpath(np["path"]).lower() not in existing_paths:
                        self.detected_projects.append(np)
                        existing_paths.add(os.path.normpath(np["path"]).lower())
                        added_count += 1
                self.populate_gallery(self.detected_projects)
                if added_count > 0:
                    self.show_friendly_banner(
                        f"✓ Appended {added_count} new project(s). Total available: {len(self.detected_projects)}",
                        is_info=True
                    )
                else:
                    self.show_friendly_banner("ℹ️ Scanned project is already in your project list.", is_info=True)
            else:
                self.show_friendly_banner(f"ℹ️ No .uproject files found in '{d}'.", is_info=False)

    def populate_gallery(self, projects):
        for w in self.gallery_scrollable.winfo_children():
            w.destroy()

        self.project_cards = {}
        self.thumbnail_images = {}
        self.icon_images = {}
        self.detected_projects = projects
        t = self.app.get_theme_config()

        if not projects:
            self.show_empty_gallery("No .uproject files found in scanned directories.")
            return

        row, col = 0, 0
        max_cols = 3

        for proj in projects:
            proj_dir = proj["path"]
            proj_name = proj["name"]

            card = tk.Frame(
                self.gallery_scrollable,
                bg=t["card_bg"],
                highlightbackground=t["card_border"],
                highlightthickness=1,
                padx=10,
                pady=10
            )
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.project_cards[proj_dir] = card

            # Header with Game Root Icon (if present) + Name
            hdr_frame = tk.Frame(card, bg=t["card_bg"])
            hdr_frame.pack(fill=tk.X, pady=(0, 4))

            if proj.get("icon"):
                icon_img = load_project_icon(proj["icon"], icon_size=(20, 20))
                if icon_img:
                    self.icon_images[proj_dir] = icon_img
                    tk.Label(hdr_frame, image=icon_img, bg=t["card_bg"]).pack(side=tk.LEFT, padx=(0, 4))

            tk.Label(hdr_frame, text=f" {proj_name} ", font=("Segoe UI", 10, "bold"), fg=t["fg"], bg=t["card_bg"]).pack(side=tk.LEFT)

            # Aspect-ratio preserved thumbnail container (only if screenshot exists)
            photo = load_project_thumbnail(proj["screenshot"], canvas_size=(230, 130))
            if photo:
                self.thumbnail_images[proj_dir] = photo
                img_lbl = tk.Label(card, image=photo, bg="#0f172a")
                img_lbl.pack(pady=(0, 4))

            tk.Label(card, text=proj_dir, font=("Segoe UI", 8), fg="#7f8c8d", bg=t["card_bg"], wraplength=230).pack(anchor="w", pady=(0, 4))

            btn_frame = tk.Frame(card, bg=t["card_bg"])
            btn_frame.pack(fill=tk.X, pady=4)

            btn = ttk.Button(btn_frame, text="Select Project", command=lambda p=proj_dir, n=proj_name: self.handle_card_selection(p, n))
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X)
            card.select_btn = btn

            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Bind mousewheel to all dynamically created cards & labels
        bind_mousewheel(self.gallery_scrollable, self.canvas_gallery)
        self.update_card_highlights()

    def show_empty_gallery(self, msg):
        t = self.app.get_theme_config()
        lbl = tk.Label(self.gallery_scrollable, text=msg, font=("Segoe UI", 11), fg=t["fg"], bg=t["bg"], justify="center")
        lbl.pack(padx=20, pady=40, expand=True)

    def verify_and_launch(self):
        b = self.base_dir_var.get()
        s = self.source_dir_var.get()
        if not b or not s:
            self.show_friendly_banner("ℹ️ Please select both a Base and a Source project first.", is_info=False)
            return
        if b == s:
            self.show_friendly_banner("ℹ️ Base and Source projects cannot be identical.", is_info=False)
            return
        self.on_launch_merger()
