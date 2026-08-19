"""
Manual INI Direct Editor & Snippet Merger
Allows developers to paste raw Unreal Engine INI snippets (e.g. from Game Animation Sample, Lyra, Forums)
and compare/merge them directly without needing whole project directories on disk.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ini_engine import parse_ini_into_sections, build_key_dict


SAMPLE_GAME_ANIMATION_INI = """[/Script/EngineSettings.GeneralProjectSettings]
ProjectName=Game Animation Sample Project
Description=Motion Matching & Trajectory Locomotion Config

[/Script/MotionWarping.MotionWarpingSettings]
bEnableMotionWarping=True
bMotionWarpingRespectRootMotion=True
MaxWarpDuration=2.500000

[/Script/PoseSearch.PoseSearchDatabase]
bEnablePoseSearch=True
PoseSearchMaxHistory=1.000000
StrideWarpingMultiplier=1.000000

[/Script/GameAnimationSample.GameAnimSettings]
bUseMotionMatchingLocomotion=True
bEnableDistanceMatching=True
bEnableOrientationWarping=True
MaxSprintSpeed=850.000000
JogSpeed=500.000000
"""

SAMPLE_MY_CUSTOM_PROJECT_INI = """[/Script/EngineSettings.GeneralProjectSettings]
ProjectName=My Action RPG Game
Description=Custom Action Combat

[/Script/MyGame.CombatSettings]
bEnableParry=True
MaxComboCount=5
DodgeStaminaCost=15.000000
"""


class ManualIniEditorFrame(tk.Frame):
    def __init__(self, parent, app, initial_base_text="", initial_source_text="", file_label="Direct INI", on_back_to_hub=None):
        self.app = app
        self.theme = self.app.get_theme_config()
        super().__init__(parent, bg=self.theme["bg"], padx=15, pady=10)
        self.on_back_to_hub = on_back_to_hub
        self.file_label = file_label

        self.build_ui(initial_base_text, initial_source_text)

    def build_ui(self, initial_base, initial_source):
        t = self.theme
        # Top Navigation Bar
        nav_bar = tk.Frame(self, bg=t["bg"])
        nav_bar.pack(fill=tk.X, pady=(0, 10))

        if self.on_back_to_hub:
            ttk.Button(nav_bar, text="⬅ Back to Project Hub", command=self.on_back_to_hub).pack(side=tk.LEFT, padx=(0, 10))

        tk.Label(
            nav_bar,
            text="📝 Manual INI Direct Editor & Snippet Merger",
            font=("Segoe UI", 12, "bold"),
            fg=t["accent"],
            bg=t["bg"]
        ).pack(side=tk.LEFT)

        # Presets & Actions
        action_bar = tk.Frame(nav_bar, bg=t["bg"])
        action_bar.pack(side=tk.RIGHT)

        ttk.Button(action_bar, text="⚡ Load GameAnimSample Preset", command=self.load_sample_preset).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_bar, text="⇄ Swap Left & Right", command=self.swap_texts).pack(side=tk.LEFT, padx=3)
        ttk.Button(action_bar, text="🔄 Clear Both", command=self.clear_texts).pack(side=tk.LEFT, padx=3)

        # Two-Column Raw Text Scratchpad
        editor_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        editor_paned.pack(fill=tk.BOTH, expand=True, pady=5)

        # Left: Base Raw Text
        left_box = ttk.LabelFrame(editor_paned, text=" 📄 Base / Target INI (Raw Text) ", padding=8)
        editor_paned.add(left_box, weight=1)

        left_toolbar = tk.Frame(left_box, bg=t["bg"])
        left_toolbar.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(left_toolbar, text="📂 Load File...", command=lambda: self.load_file_into(self.txt_base)).pack(side=tk.LEFT)
        ttk.Button(left_toolbar, text="💾 Save Base...", command=lambda: self.save_text_as(self.txt_base.get("1.0", tk.END))).pack(side=tk.RIGHT)

        self.txt_base = tk.Text(left_box, wrap=tk.NONE, font=("Consolas", 10), bg=t["card_bg"], fg=t["fg"], insertbackground=t["fg"], padx=6, pady=6)
        scroll_b_y = ttk.Scrollbar(left_box, orient=tk.VERTICAL, command=self.txt_base.yview)
        scroll_b_x = ttk.Scrollbar(left_box, orient=tk.HORIZONTAL, command=self.txt_base.xview)
        self.txt_base.configure(yscrollcommand=scroll_b_y.set, xscrollcommand=scroll_b_x.set)

        scroll_b_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_b_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.txt_base.pack(fill=tk.BOTH, expand=True)

        # Right: Source Raw Text
        right_box = ttk.LabelFrame(editor_paned, text=" 📄 Source / Mod INI (Raw Text) ", padding=8)
        editor_paned.add(right_box, weight=1)

        right_toolbar = tk.Frame(right_box, bg=t["bg"])
        right_toolbar.pack(fill=tk.X, pady=(0, 4))
        ttk.Button(right_toolbar, text="📂 Load File...", command=lambda: self.load_file_into(self.txt_source)).pack(side=tk.LEFT)
        ttk.Button(right_toolbar, text="💾 Save Source...", command=lambda: self.save_text_as(self.txt_source.get("1.0", tk.END))).pack(side=tk.RIGHT)

        self.txt_source = tk.Text(right_box, wrap=tk.NONE, font=("Consolas", 10), bg=t["card_bg"], fg=t["fg"], insertbackground=t["fg"], padx=6, pady=6)
        scroll_s_y = ttk.Scrollbar(right_box, orient=tk.VERTICAL, command=self.txt_source.yview)
        scroll_s_x = ttk.Scrollbar(right_box, orient=tk.HORIZONTAL, command=self.txt_source.xview)
        self.txt_source.configure(yscrollcommand=scroll_s_y.set, xscrollcommand=scroll_s_x.set)

        scroll_s_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_s_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.txt_source.pack(fill=tk.BOTH, expand=True)

        # Bottom Action Bar
        bottom_bar = tk.Frame(self, bg=t["bg"], pady=8)
        bottom_bar.pack(fill=tk.X)

        tk.Label(
            bottom_bar,
            text="💡 Tip: Paste raw INI text directly into both boxes to compare sections and merge keys.",
            font=("Segoe UI", 9, "italic"),
            fg=t["status_fg"],
            bg=t["bg"]
        ).pack(side=tk.LEFT)

        btn_merge_now = tk.Button(
            bottom_bar,
            text="🚀 Compare & Merge Raw Texts Now",
            font=("Segoe UI", 10, "bold"),
            bg=t["source_border"],
            fg="#ffffff",
            relief="raised",
            padx=14,
            pady=6,
            command=self.execute_raw_merge
        )
        btn_merge_now.pack(side=tk.RIGHT)

        # Populate initial texts
        if initial_base:
            self.txt_base.insert("1.0", initial_base)
        else:
            self.txt_base.insert("1.0", SAMPLE_MY_CUSTOM_PROJECT_INI)

        if initial_source:
            self.txt_source.insert("1.0", initial_source)
        else:
            self.txt_source.insert("1.0", SAMPLE_GAME_ANIMATION_INI)

    def load_file_into(self, text_widget):
        f = filedialog.askopenfilename(filetypes=[("INI Files", "*.ini"), ("All Files", "*.*")])
        if f:
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()
                text_widget.delete("1.0", tk.END)
                text_widget.insert("1.0", content)
            except Exception as e:
                self.app.show_error_popup("Read Failed", f"Could not read file:\n{e}")

    def save_text_as(self, content):
        f = filedialog.asksaveasfilename(defaultextension=".ini", filetypes=[("INI Files", "*.ini"), ("All Files", "*.*")])
        if f:
            try:
                with open(f, 'w', encoding='utf-8') as file:
                    file.write(content)
                messagebox.showinfo("Saved", f"File saved successfully to:\n{f}")
            except Exception as e:
                self.app.show_error_popup("Save Failed", f"Could not save file:\n{e}")

    def swap_texts(self):
        b = self.txt_base.get("1.0", tk.END)
        s = self.txt_source.get("1.0", tk.END)
        self.txt_base.delete("1.0", tk.END)
        self.txt_base.insert("1.0", s)
        self.txt_source.delete("1.0", tk.END)
        self.txt_source.insert("1.0", b)

    def clear_texts(self):
        self.txt_base.delete("1.0", tk.END)
        self.txt_source.delete("1.0", tk.END)

    def load_sample_preset(self):
        self.txt_base.delete("1.0", tk.END)
        self.txt_base.insert("1.0", SAMPLE_MY_CUSTOM_PROJECT_INI)
        self.txt_source.delete("1.0", tk.END)
        self.txt_source.insert("1.0", SAMPLE_GAME_ANIMATION_INI)

    def execute_raw_merge(self):
        b_lines = self.txt_base.get("1.0", tk.END).splitlines(keepends=True)
        s_lines = self.txt_source.get("1.0", tk.END).splitlines(keepends=True)

        if not "".join(b_lines).strip() and not "".join(s_lines).strip():
            messagebox.showinfo("Info", "Please paste or type INI text into at least one of the boxes.")
            return

        # Create temporary files for the visual comparator
        import tempfile
        t_base = tempfile.NamedTemporaryFile(delete=False, suffix="_base.ini", mode="w", encoding="utf-8")
        t_base.writelines(b_lines)
        t_base.close()

        t_source = tempfile.NamedTemporaryFile(delete=False, suffix="_source.ini", mode="w", encoding="utf-8")
        t_source.writelines(s_lines)
        t_source.close()

        # Switch to merger frame using temporary project folders
        self.app.base_project_dir.set(os.path.dirname(t_base.name))
        self.app.source_project_dir.set(os.path.dirname(t_source.name))
        self.app.show_merger_page()
