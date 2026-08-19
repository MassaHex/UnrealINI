"""
Visual INI Merger & Comparator Workspace
Allows granular key-by-key resolution, bulk decisions, direct UE project config writes, and smooth mouse wheel scrolling.
"""
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import bind_mousewheel
from ini_engine import (
    discover_project_inis,
    compute_section_diffs,
    compile_merged_content
)


class IniMergerFrame(tk.Frame):
    MAX_INI_BYTES = 100 * 1024

    def __init__(self, parent, app, base_dir, source_dir, on_back_to_hub):
        self.app = app
        t= self.app.get_theme_config()
        super().__init__(parent, bg=t["bg"], padx=10, pady=5)
        self.base_dir = base_dir
        self.source_dir = source_dir
        self.on_back_to_hub = on_back_to_hub

        self.discovered_files = {}
        self.cached_editors = {}
        self.current_active_rel_path = None

        self.build_ui()
        self.scan_and_populate()

    def build_ui(self):
        t= self.app.get_theme_config()
        # Top Navigation Bar
        nav_frame = ttk.Frame(self, padding=6)
        nav_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Button(nav_frame, text="⬅ Back to Project Hub", command=self.on_back_to_hub).pack(side=tk.LEFT)

        ttk.Label(
            nav_frame,
            text=f"  Base: {os.path.basename(self.base_dir)}  ↔  Source: {os.path.basename(self.source_dir)}",
            font=("Segoe UI", 10, "bold"),
            foreground=t["top_fg"]
        ).pack(side=tk.LEFT, padx=10)

        # Paned Window (Left = Tree Explorer, Right = Comparator Workspace)
        self.paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True, pady=5)

        # Left File Explorer Panel
        left_panel = ttk.LabelFrame(self.paned, text=" 📑 Discovered INI Files ", padding=6)
        self.paned.add(left_panel, weight=1)

        self.file_tree = ttk.Treeview(left_panel, selectmode="browse", show="tree")
        self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.file_tree.bind("<<TreeviewSelect>>", self.on_file_selected)

        tree_scroll = ttk.Scrollbar(left_panel, orient="vertical", command=self.file_tree.yview)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_tree.configure(yscrollcommand=tree_scroll.set)

        # Right Editor Container
        self.right_container = ttk.Frame(self.paned)
        self.paned.add(self.right_container, weight=4)

        self.placeholder_frame = ttk.LabelFrame(self.right_container, text=" ⚙️ Live Visual INI Merger ", padding=10)
        self.placeholder_frame.pack(fill=tk.BOTH, expand=True)
        ttk.Label(
            self.placeholder_frame,
            text="👈 Select an INI file from the left panel to compare sections and merge keys.",
            font=("Segoe UI", 11),
            foreground=t["status_fg"]
        ).pack(expand=True)

    def scan_and_populate(self):
        self.discovered_files = discover_project_inis(self.base_dir, self.source_dir)
        self.file_tree.delete(*self.file_tree.get_children())

        first_rel = None
        for rel_path in sorted(self.discovered_files.keys()):
            if not first_rel:
                first_rel = rel_path
            self.file_tree.insert("", "end", text=f" 📄 {rel_path}", values=(rel_path,))

        if first_rel and self.file_tree.get_children():
            self.file_tree.selection_set(self.file_tree.get_children()[0])

    def on_file_selected(self, event):
        items = self.file_tree.selection()
        if not items:
            return
        rel_path = self.file_tree.item(items[0])["values"][0]
        if rel_path == self.current_active_rel_path:
            return

        file_info = self.discovered_files[rel_path]
        oversized = []
        for label, file_path in (("Base", file_info["base_path"]), ("Source", file_info["source_path"])):
            if file_path and os.path.exists(file_path) and os.path.getsize(file_path) > self.MAX_INI_BYTES:
                oversized.append(f"{label}: {os.path.basename(file_path)}")
        if oversized:
            messagebox.showwarning(
                "INI File Too Large",
                "This file was rejected before parsing because it exceeds "
                f"{self.MAX_INI_BYTES // 1024} KB:\n\n" + "\n".join(oversized)
            )
            return

        self.current_active_rel_path = rel_path

        if self.placeholder_frame.winfo_exists():
            self.placeholder_frame.pack_forget()

        for p, data in self.cached_editors.items():
            data["frame"].pack_forget()

        if rel_path in self.cached_editors:
            self.cached_editors[rel_path]["frame"].pack(fill=tk.BOTH, expand=True)
        else:
            frame = self.create_editor_for_file(rel_path, file_info["base_path"], file_info["source_path"])
            frame.pack(fill=tk.BOTH, expand=True)

    def create_editor_for_file(self, rel_path, base_path, source_path):
        t= self.app.get_theme_config()
        wrapper = ttk.LabelFrame(self.right_container, text=f" ⚙️ Visual INI Comparator: {rel_path} ", padding=8)

        # Toolbar
        control_bar = ttk.Frame(wrapper, padding=4)
        control_bar.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(control_bar, text=f"File: {os.path.basename(rel_path)}", style="Header.TLabel").pack(side=tk.LEFT, padx=4)

        ttk.Button(control_bar, text="⚡ All Left (Base)", command=lambda: self.bulk_set(rel_path, "left")).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_bar, text="⚡ All Right (Source)", command=lambda: self.bulk_set(rel_path, "right")).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_bar, text="⚡ All Skip", command=lambda: self.bulk_set(rel_path, "skip")).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_bar, text="🔄 Reset", command=lambda: self.bulk_reset(rel_path)).pack(side=tk.LEFT, padx=4)

        ttk.Separator(control_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6)

        ttk.Button(control_bar, text="💾 Overwrite Base", command=lambda: self.save_file(rel_path, base_path, "Base")).pack(side=tk.RIGHT, padx=2)
        ttk.Button(control_bar, text="💾 Overwrite Source", command=lambda: self.save_file(rel_path, source_path, "Source")).pack(side=tk.RIGHT, padx=2)
        ttk.Button(control_bar, text="💾 Save As...", command=lambda: self.save_file(rel_path, None, "Custom")).pack(side=tk.RIGHT, padx=2)

        # Scrollable comparison area
        container = ttk.Frame(wrapper)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, highlightthickness=0, background=t["bg"])
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=t["bg"])

        scroll_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(scroll_window, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Bind mouse wheel across canvas & diff rows
        bind_mousewheel(canvas, canvas)
        bind_mousewheel(scrollable_frame, canvas)

        # Compute diff rows
        diff_rows = compute_section_diffs(base_path, source_path)
        row_items = []
        row_idx = 1

        ttk.Label(scrollable_frame, text="Left / Target (Base Project)", font=("Segoe UI", 9, "bold"), foreground=t["base_border"]).grid(row=0, column=1, sticky="w", padx=6, pady=4)
        ttk.Label(scrollable_frame, text="Right / Mod (Source Project)", font=("Segoe UI", 9, "bold"), foreground=t["source_border"]).grid(row=0, column=2, sticky="w", padx=6, pady=4)

        for item in diff_rows:
            if item["type"] == "section":
                sec_lbl = tk.Label(
                    scrollable_frame,
                    text=f"  {item['text']}",
                    bg=t["top_bg"],
                    fg=t["top_fg"],
                    font=("Segoe UI", 10, "bold"),
                    anchor="w"
                )
                sec_lbl.grid(row=row_idx, column=0, columnspan=4, sticky="ew", pady=(10, 2))
                row_items.append({"type": "section", "text": item["text"]})
                row_idx += 1
            else:
                var = tk.StringVar(value=item["default_choice"])

                row_frame = ttk.Frame(scrollable_frame)
                row_frame.grid(row=row_idx, column=0, columnspan=4, sticky="ew", pady=1)

                choice_frame = ttk.Frame(row_frame)
                choice_frame.pack(side=tk.LEFT, padx=4)

                ttk.Radiobutton(choice_frame, text="Left", variable=var, value="left").pack(side=tk.LEFT, padx=1)
                ttk.Radiobutton(choice_frame, text="Right", variable=var, value="right").pack(side=tk.LEFT, padx=1)
                ttk.Radiobutton(choice_frame, text="Skip", variable=var, value="skip").pack(side=tk.LEFT, padx=1)

                tk.Label(
                    row_frame,
                    text=item["left_text"],
                    anchor="w",
                    width=42,
                    background=item["bg_color"],
                    relief="solid",
                    bd=1,
                    font=("Consolas", 9)
                ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

                tk.Label(
                    row_frame,
                    text=item["right_text"],
                    anchor="w",
                    width=42,
                    background=item["bg_color"],
                    relief="solid",
                    bd=1,
                    font=("Consolas", 9)
                ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)

                row_items.append({
                    "type": "line",
                    "var": var,
                    "default_choice": item["default_choice"],
                    "left_text": item["left_text"],
                    "right_text": item["right_text"]
                })
                row_idx += 1

        bind_mousewheel(scrollable_frame, canvas)

        self.cached_editors[rel_path] = {
            "frame": wrapper,
            "row_items": row_items
        }
        return wrapper

    def bulk_set(self, rel_path, choice):
        if rel_path in self.cached_editors:
            for item in self.cached_editors[rel_path]["row_items"]:
                if item["type"] == "line":
                    item["var"].set(choice)

    def bulk_reset(self, rel_path):
        if rel_path in self.cached_editors:
            for item in self.cached_editors[rel_path]["row_items"]:
                if item["type"] == "line":
                    item["var"].set(item["default_choice"])

    def save_file(self, rel_path, default_path, mode_name):
        if rel_path not in self.cached_editors:
            return

        if mode_name == "Custom" or not default_path:
            target_path = filedialog.asksaveasfilename(
                initialfile=os.path.basename(rel_path),
                filetypes=[("INI Files", "*.ini"), ("All Files", "*.*")]
            )
            if not target_path:
                return
        else:
            target_path = default_path
            if not os.path.exists(target_path):
                base_dir = self.base_dir if mode_name == "Base" else self.source_dir
                target_path = os.path.join(base_dir, rel_path)

            if not messagebox.askyesno(
                "Confirm Direct Overwrite",
                f"Are you sure you want to write the merged configuration directly to {mode_name}?\n\n{target_path}"
            ):
                return

        editor_data = self.cached_editors[rel_path]
        merged_text = compile_merged_content(editor_data["row_items"])

        try:
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(merged_text)
            messagebox.showinfo("Success", f"Successfully saved configuration to:\n{target_path}")
        except Exception as e:
            self.app.show_error_popup("Save Failed", f"Could not write file:\n{e}")
