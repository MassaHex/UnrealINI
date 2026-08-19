"""
Unreal Engine INI Section Parser & Visual Comparator Engine
Handles [Section.Names], Key=Value mapping, comment preservation, and line diffs.
"""
import os
import glob


def discover_project_inis(base_dir, source_dir):
    """
    Finds all relative INI paths in both Base and Source project directories
    (e.g., Config/DefaultEngine.ini, Config/DefaultGame.ini, Config/DefaultInput.ini).
    """
    if not os.path.isdir(base_dir) or not os.path.isdir(source_dir):
        return {}

    base_inis = glob.glob(os.path.join(base_dir, "**", "*.ini"), recursive=True)
    source_inis = glob.glob(os.path.join(source_dir, "**", "*.ini"), recursive=True)

    base_rel = {os.path.relpath(p, base_dir).replace('\\', '/'): p for p in base_inis}
    source_rel = {os.path.relpath(p, source_dir).replace('\\', '/'): p for p in source_inis}

    all_rel_paths = sorted(list(set(base_rel.keys()).union(set(source_rel.keys()))))
    discovered = {}
    for rel in all_rel_paths:
        discovered[rel] = {
            "base_path": base_rel.get(rel),
            "source_path": source_rel.get(rel)
        }
    return discovered


def parse_ini_into_sections(lines):
    """Parses INI lines into categorized section blocks."""
    sections = {}
    current_sec = ""
    sections[current_sec] = []
    for line in lines:
        clean_line = line.strip()
        if clean_line.startswith('[') and clean_line.endswith(']'):
            current_sec = clean_line
            if current_sec not in sections:
                sections[current_sec] = []
        else:
            if clean_line:
                sections[current_sec].append(line.rstrip('\r\n'))
    return sections


def build_key_dict(lines):
    """Maps keys to full raw INI statement lines preserving order."""
    d = {}
    order = []
    for l in lines:
        if '=' in l:
            k = l.split('=', 1)[0].strip()
            if k not in d:
                order.append(k)
            d[k] = l
        else:
            order.append(l)
            d[l] = l
    return d, order


def compute_section_diffs(base_path, source_path):
    """
    Reads base and source INI files and produces aligned comparison rows.
    Returns: (all_sections, row_definitions)
    """
    left_lines = []
    right_lines = []
    if base_path and os.path.exists(base_path):
        with open(base_path, 'r', encoding='utf-8', errors='ignore') as f:
            left_lines = f.readlines()
    if source_path and os.path.exists(source_path):
        with open(source_path, 'r', encoding='utf-8', errors='ignore') as f:
            right_lines = f.readlines()

    left_sections = parse_ini_into_sections(left_lines)
    right_sections = parse_ini_into_sections(right_lines)

    all_sections = list(left_sections.keys())
    for sec in right_sections.keys():
        if sec not in all_sections:
            all_sections.append(sec)

    rows = []
    for sec in all_sections:
        if sec != "":
            rows.append({
                "type": "section",
                "text": sec
            })

        l_lines = left_sections.get(sec, [])
        r_lines = right_sections.get(sec, [])

        l_dict, l_order = build_key_dict(l_lines)
        r_dict, r_order = build_key_dict(r_lines)

        combined_keys = list(l_order)
        for k in r_order:
            if k not in combined_keys:
                combined_keys.append(k)

        for k in combined_keys:
            in_left = k in l_dict
            in_right = k in r_dict

            default_choice = "left"
            lbl_left_text = ""
            lbl_right_text = ""
            bg_color = "#ffffff"
            status = "identical"

            if in_left and in_right:
                l_val = l_dict[k]
                r_val = r_dict[k]
                lbl_left_text = l_val
                lbl_right_text = r_val
                if l_val == r_val:
                    default_choice = "left"
                    bg_color = "#ffffff"
                    status = "identical"
                else:
                    default_choice = "right"  # Source update candidate
                    bg_color = "#fef9e7"      # Yellow warning
                    status = "conflict"
            elif in_left and not in_right:
                default_choice = "left"
                lbl_left_text = l_dict[k]
                lbl_right_text = ""
                bg_color = "#fadbd8"          # Red/pink Base only
                status = "left-only"
            elif not in_left and in_right:
                default_choice = "right"
                lbl_left_text = ""
                lbl_right_text = r_dict[k]
                bg_color = "#d4efdf"          # Green Source only
                status = "right-only"

            rows.append({
                "type": "line",
                "key": k,
                "default_choice": default_choice,
                "left_text": lbl_left_text,
                "right_text": lbl_right_text,
                "bg_color": bg_color,
                "status": status
            })

    return rows


def compile_merged_content(row_items):
    """Assembles the final merged INI text based on user choices."""
    merged_lines = []
    for item in row_items:
        if item["type"] == "section":
            if item["text"] != "":
                merged_lines.append("\n" + item["text"] + "\n")
        elif item["type"] == "line":
            choice = item["var"].get()
            if choice == "left" and item["left_text"] != "":
                merged_lines.append(item["left_text"] + "\n")
            elif choice == "right" and item["right_text"] != "":
                merged_lines.append(item["right_text"] + "\n")
            # 'skip' outputs nothing
    return "".join(merged_lines)
