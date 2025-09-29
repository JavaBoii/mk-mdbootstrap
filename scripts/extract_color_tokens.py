import os
import re
import json
import csv
from collections import defaultdict, OrderedDict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
TARGET_PATHS = [
    os.path.join(REPO_ROOT, "src", "scss", "bootstrap"),
    os.path.join(REPO_ROOT, "src", "scss", "bootstrap-rtl-fix"),
    os.path.join(REPO_ROOT, "src", "scss", "free"),
    os.path.join(REPO_ROOT, "src", "scss", "custom"),
]
EXTRA_FILES = [
    os.path.join(REPO_ROOT, "src", "scss", "mdb.free.scss"),
]

THEME_COLOR_NAMES = [
    "primary",
    "secondary",
    "success",
    "info",
    "warning",
    "danger",
    "light",
    "dark",
]

SEMANTIC_KEYWORDS = {
    "theme-color": [
        "primary",
        "secondary",
        "success",
        "info",
        "warning",
        "danger",
        "light",
        "dark",
    ],
    "surface": [
        "bg",
        "background",
        "surface",
        "body",
        "card",
        "modal",
        "dropdown",
        "offcanvas",
        "list-group",
        "table",
        "popover",
        "tooltip",
        "toast",
        "navbar",
    ],
    "text": [
        "text",
        "font",
        "heading",
        "emphasis",
        "muted",
        "caption",
        "placeholder",
        "body",
        "subtitle",
        "lead",
    ],
    "border": [
        "border",
        "outline",
        "divider",
        "rule",
    ],
    "link": [
        "link",
    ],
    "state": [
        "focus",
        "hover",
        "active",
        "visited",
        "disabled",
        "checked",
        "invalid",
        "valid",
        "warning",
        "danger",
        "success",
    ],
    "utility": [
        "utility",
        "helpers",
        "accent",
    ],
}

COLOR_NAME_HINTS = {
    "white",
    "black",
    "gray",
    "grey",
    "blue",
    "indigo",
    "purple",
    "pink",
    "red",
    "orange",
    "yellow",
    "green",
    "teal",
    "cyan",
    "amber",
    "lime",
    "brown",
    "deep",
}

PREFIX_TOKEN = "#{$prefix}"

CSS_VAR_PATTERN = re.compile(r"(--[\w-]+)\s*:\s*(.+?);", re.S)

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.S)
LINE_COMMENT_RE = re.compile(r"^\s*//.*$", re.M)

PREFIX_INTERPOLATION_RE = re.compile(r"--#\{\$prefix\}")
PREFIX_INTERPOLATION_SIMPLE_RE = re.compile(r"#\{\$prefix\}")

VAR_TOKEN_RE = re.compile(r"\$[\w-]+|var\(--[\w-]+\)|--[\w-]+|color-contrast\([^\)]+\)|tint-color\([^\)]+\)|shade-color\([^\)]+\)|shift-color\([^\)]+\)|rgba\([^\)]+\)|RGBA\([^\)]+\)|mix\([^\)]+\)")

ALPHA_VAR_RE = re.compile(r"rgba\(var\(--bs-([\w-]+)-rgb\),\s*([^\)]+)\)", re.I)
ALPHA_VAR_UPPER_RE = re.compile(r"RGBA\(var\(--bs-([\w-]+)-rgb\),\s*([^\)]+)\)", re.I)
ALPHA_TO_RGB_RE = re.compile(r"rgba\((var\(--bs-[\w-]+-rgb\)),\s*([^\)]+)\)", re.I)
ALPHA_COLOR_RE = re.compile(r"rgba\(\s*\$([\w-]+)\s*,\s*([^\)]+)\)", re.I)

FUNCTION_REPLACEMENTS = {
    "tint-color": "tint",
    "shade-color": "shade",
    "shift-color": "shift",
    "color-contrast": "contrast",
    "rgba": "rgba",
    "RGBA": "rgba",
}

LAYER_RULES = [
    ("bootstrap-core", os.path.join("src", "scss", "bootstrap")),
    ("bootstrap-core", os.path.join("src", "scss", "bootstrap-rtl-fix")),
    ("mdbootstrap", os.path.join("src", "scss", "free")),
    ("custom", os.path.join("src", "scss", "custom")),
]


def normalize_path(path: str) -> str:
    rel = os.path.relpath(path, REPO_ROOT)
    return rel.replace(os.sep, "/")


def strip_comments(text: str) -> str:
    def repl(match: re.Match) -> str:
        return "\n" * match.group(0).count("\n")

    no_block = re.sub(BLOCK_COMMENT_RE, repl, text)
    no_line = re.sub(LINE_COMMENT_RE, "", no_block)
    return no_line


def replace_prefix_tokens(text: str) -> str:
    text = re.sub(PREFIX_INTERPOLATION_RE, "--bs-", text)
    text = re.sub(PREFIX_INTERPOLATION_SIMPLE_RE, "bs-", text)
    return text


def clean_value(value: str) -> str:
    value = value.strip()
    value = replace_prefix_tokens(value)
    value = re.sub(r"#\{\$([\w-]+)\}", r"$\1", value)
    value = re.sub(r"#\{([^\}]+)\}", r"\1", value)
    value = re.sub(r"\s*!default", "", value)
    value = re.sub(r"\s*!global", "", value)
    value = re.sub(r"\s*!important", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def is_color_related(name: str, value: str) -> bool:
    lowered = name.lower()
    if any(token in lowered for token in [
        "color",
        "bg",
        "background",
        "shade",
        "tint",
        "gradient",
        "mark",
        "code",
        "link",
        "text",
        "body",
        "emphasis",
        "highlight",
        "tone",
        "palette",
        "surface",
        "shadow",
    ]):
        return True
    if any(name.lower().startswith(prefix) or f"-{prefix}" in lowered for prefix in COLOR_NAME_HINTS):
        return True
    value_lower = value.lower()
    if re.search(r"#[0-9a-fA-F]{3,8}", value_lower):
        return True
    if any(keyword in value_lower for keyword in [
        "rgb",
        "rgba",
        "hsl",
        "tint",
        "shade",
        "shift",
        "contrast",
        "$white",
        "$black",
        "$gray",
        "mix(",
    ]):
        return True
    return False


def detect_layer(path: str) -> str:
    rel = normalize_path(path)
    for layer, prefix in LAYER_RULES:
        if rel.startswith(prefix):
            return layer
    if rel.endswith("mdb.free.scss"):
        return "mdbootstrap"
    return "other"


def classify_semantic(name: str) -> str:
    lowered = name.lower()
    if any(lowered.startswith(theme) or f"-{theme}" in lowered for theme in THEME_COLOR_NAMES):
        return "theme-color"
    if "palette" in lowered or "mdb-" in lowered:
        return "palette"
    for semantic, tokens in SEMANTIC_KEYWORDS.items():
        if any(token in lowered for token in tokens):
            return semantic
    if "state" in lowered or "status" in lowered:
        return "state"
    if "utility" in lowered:
        return "utility"
    return "other"


def normalize_dependency(token: str) -> str:
    token = token.strip()
    if token.startswith("var(--bs-"):
        base = token[9:-1]
        return base
    if token.startswith("var(--mdb-"):
        base = token[10:-1]
        return base
    if token.startswith("--bs-"):
        return token[5:]
    if token.startswith("--mdb-"):
        return token[6:]
    if token.startswith("$"):
        return token[1:]
    if token.startswith("contrast("):
        inner = token[len("contrast("):-1]
        return normalize_dependency(inner)
    match = re.match(r"mix\(([^,]+),", token)
    if match:
        return normalize_dependency(match.group(1).strip())
    return token


def extract_dependencies(value: str) -> list:
    tokens = set()
    for match in re.finditer(r"\$[\w-]+|var\(--bs-[\w-]+\)|var\(--mdb-[\w-]+\)|--bs-[\w-]+|--mdb-[\w-]+", value):
        tokens.add(normalize_dependency(match.group(0)))
    deps = sorted(t for t in tokens if t)
    return deps


def derive_expression(value: str) -> tuple[str, list, bool]:
    raw = value
    alpha_only = False
    derivation = None
    deps = []

    lower = raw.lower()
    if raw.startswith("$") and " " not in raw:
        derivation = f"alias: {raw[1:]}"
        deps = [raw[1:]]
        return derivation, deps, alpha_only
    if raw.startswith("var(--bs-") and raw.endswith(")"):
        base = raw[9:-1]
        derivation = f"alias: {base}"
        deps = [base]
        return derivation, deps, alpha_only
    if raw.startswith("var(--mdb-") and raw.endswith(")"):
        base = raw[10:-1]
        derivation = f"alias: {base}"
        deps = [base]
        return derivation, deps, alpha_only

    m = re.fullmatch(ALPHA_VAR_RE, raw)
    if not m:
        m = re.fullmatch(ALPHA_VAR_UPPER_RE, raw)
    if m:
        base = m.group(1)
        alpha = m.group(2).strip()
        derivation = f"alpha({base}, {alpha})"
        deps = [base]
        alpha_only = True
        return derivation, deps, alpha_only

    m = re.fullmatch(ALPHA_COLOR_RE, raw)
    if m:
        base = m.group(1)
        alpha = m.group(2).strip()
        derivation = f"alpha({base}, {alpha})"
        deps = [base]
        alpha_only = True
        return derivation, deps, alpha_only

    replacements = raw
    for src, dst in FUNCTION_REPLACEMENTS.items():
        replacements = replacements.replace(src + "(", dst + "(")
    replacements = replacements.replace("to-rgb(", "to-rgb(")
    replacements = replacements.replace("#{", "")
    replacements = replacements.replace("}", "")
    if replacements != raw:
        derivation = replacements
    else:
        derivation = raw

    deps = extract_dependencies(raw)

    # Detect alpha(var(--bs-*-rgb), value) patterns without direct match
    m = re.search(r"rgba\(var\(--bs-([\w-]+)-rgb\),\s*([^\)]+)\)", raw, re.I)
    if m:
        base = m.group(1)
        alpha = m.group(2).strip()
        derivation = f"alpha({base}, {alpha})"
        deps = [base]
        alpha_only = True
        return derivation, deps, alpha_only

    return derivation, deps, alpha_only


def determine_mode_map(text: str) -> dict:
    text_no_comments = strip_comments(text)
    text_no_comments = replace_prefix_tokens(text_no_comments)
    lines = text_no_comments.splitlines()
    mode_stack = ["any"]
    pending = ""
    mode_by_line = ["any"] * len(lines)

    for idx, line in enumerate(lines):
        working = pending + line
        search_pos = 0
        while True:
            brace_index = working.find("{", search_pos)
            if brace_index == -1:
                break
            selector = working[:brace_index].strip()
            new_mode = mode_stack[-1]
            selector_lower = selector.lower()
            if "data-bs-theme" in selector_lower and "dark" in selector_lower:
                new_mode = "dark"
            elif "data-bs-theme" in selector_lower and "light" in selector_lower:
                new_mode = "light"
            elif "color-mode(" in selector_lower:
                if "dark" in selector_lower:
                    new_mode = "dark"
                elif "light" in selector_lower:
                    new_mode = "light"
            elif selector_lower.startswith(":root"):
                if new_mode == "any":
                    new_mode = "light"
            mode_stack.append(new_mode)
            working = working[brace_index + 1 :]
            search_pos = 0
        pending = working

        current_mode = mode_stack[-1]
        mode_by_line[idx] = current_mode

        close_count = line.count("}")
        for _ in range(close_count):
            if len(mode_stack) > 1:
                mode_stack.pop()
        if close_count and pending:
            pending = ""

    return {idx + 1: mode for idx, mode in enumerate(mode_by_line)}


def parse_scss_variables(path: str) -> list:
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    text_no_comments = strip_comments(text)
    text_no_comments = replace_prefix_tokens(text_no_comments)

    length = len(text_no_comments)
    idx = 0
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    while idx < length:
        char = text_no_comments[idx]
        if char == "\"" or char == "'":
            quote = char
            idx += 1
            while idx < length:
                if text_no_comments[idx] == "\\":
                    idx += 2
                    continue
                if text_no_comments[idx] == quote:
                    idx += 1
                    break
                idx += 1
            continue
        if char == "(":
            paren_depth += 1
            idx += 1
            continue
        if char == ")":
            paren_depth = max(paren_depth - 1, 0)
            idx += 1
            continue
        if char == "[":
            bracket_depth += 1
            idx += 1
            continue
        if char == "]":
            bracket_depth = max(bracket_depth - 1, 0)
            idx += 1
            continue
        if char == "{":
            brace_depth += 1
            idx += 1
            continue
        if char == "}":
            brace_depth = max(brace_depth - 1, 0)
            idx += 1
            continue

        if char == "$" and paren_depth == 0:
            start_idx = idx
            idx += 1
            while idx < length and re.match(r"[\w-]", text_no_comments[idx]):
                idx += 1
            name = text_no_comments[start_idx + 1 : idx]
            temp_idx = idx
            while temp_idx < length and text_no_comments[temp_idx].isspace():
                temp_idx += 1
            if temp_idx >= length or text_no_comments[temp_idx] != ":":
                idx = temp_idx
                continue
            temp_idx += 1
            while temp_idx < length and text_no_comments[temp_idx].isspace():
                temp_idx += 1
            value_start = temp_idx
            inner_paren = 0
            inner_brace = 0
            inner_bracket = 0
            while temp_idx < length:
                ch = text_no_comments[temp_idx]
                if ch == "\"" or ch == "'":
                    quote = ch
                    temp_idx += 1
                    while temp_idx < length:
                        if text_no_comments[temp_idx] == "\\":
                            temp_idx += 2
                            continue
                        if text_no_comments[temp_idx] == quote:
                            temp_idx += 1
                            break
                        temp_idx += 1
                    continue
                if ch == "(":
                    inner_paren += 1
                elif ch == ")":
                    inner_paren = max(inner_paren - 1, 0)
                elif ch == "[":
                    inner_bracket += 1
                elif ch == "]":
                    inner_bracket = max(inner_bracket - 1, 0)
                elif ch == "{":
                    inner_brace += 1
                elif ch == "}":
                    inner_brace = max(inner_brace - 1, 0)
                elif ch == ";" and inner_paren == 0 and inner_brace == 0 and inner_bracket == 0:
                    value_end = temp_idx
                    break
                temp_idx += 1
            else:
                idx += 1
                continue

            raw_value = text_no_comments[value_start:value_end]
            value = clean_value(raw_value)
            if not is_color_related(name, value):
                idx = temp_idx + 1
                continue
            line_no = text_no_comments.count("\n", 0, start_idx) + 1
            entries.append({
                "name": f"${name}",
                "type": "scss-var" if not value.strip().startswith("(") else "scss-map",
                "layer": detect_layer(path),
                "semantic_group": classify_semantic(name),
                "mode": "any",
                "source_file": normalize_path(path),
                "line": line_no,
                "value_raw": value,
            })
            idx = temp_idx + 1
            continue

        idx += 1

    return entries


def parse_css_variables(path: str, mode_map: dict) -> list:
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    text_no_comments = strip_comments(text)
    text_no_comments = replace_prefix_tokens(text_no_comments)

    for match in re.finditer(CSS_VAR_PATTERN, text_no_comments):
        name = match.group(1)
        raw_value = match.group(2).strip()
        value = clean_value(raw_value)
        start = match.start(0)
        line_no = text_no_comments.count("\n", 0, start) + 1
        mode = mode_map.get(line_no, "any")
        if not is_color_related(name, value):
            continue
        entries.append({
            "name": name,
            "type": "css-var",
            "layer": detect_layer(path),
            "semantic_group": classify_semantic(name),
            "mode": mode,
            "source_file": normalize_path(path),
            "line": line_no,
            "value_raw": value,
        })
    return entries


def enrich_entries(entries: list) -> list:
    seen = {}
    for entry in entries:
        name = entry["name"]
        etype = entry["type"]
        value = entry["value_raw"]
        derivation, deps, alpha_only = derive_expression(value)
        entry["derivation"] = derivation
        entry["depends_on"] = deps
        entry["alpha_only"] = alpha_only
        entry["is_override"] = False
        entry["notes"] = ""
        key = (etype, name)
        if key not in seen:
            seen[key] = entry
        else:
            entry["is_override"] = True
    return entries


def ensure_out_paths():
    out_dir = os.path.join(REPO_ROOT, "out")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "components"), exist_ok=True)
    return out_dir


def parse_theme_colors(entries: list) -> OrderedDict:
    theme_map_entry = next(
        (e for e in entries if e["name"] == "$theme-colors" and e["type"] == "scss-map"),
        None,
    )
    theme_colors = OrderedDict()
    if not theme_map_entry:
        return theme_colors
    value = theme_map_entry["value_raw"]
    value = value.strip()
    if value.endswith("!default"):
        value = value[:-8].strip()
    if value.startswith("(") and value.endswith(")"):
        content = value[1:-1].strip()
    else:
        content = value

    entries_list = []
    current = ""
    depth = 0
    in_string = None
    for char in content:
        if char in "'\"":
            if in_string == char:
                in_string = None
            elif not in_string:
                in_string = char
        elif char == "(" and not in_string:
            depth += 1
        elif char == ")" and not in_string:
            depth -= 1
        if char == "," and depth == 0 and not in_string:
            if current.strip():
                entries_list.append(current.strip())
            current = ""
        else:
            current += char
    if current.strip():
        entries_list.append(current.strip())

    for item in entries_list:
        if ":" not in item:
            continue
        key_part, value_part = item.split(":", 1)
        key_part = key_part.strip().strip("'\"")
        value_part = clean_value(value_part)
        theme_colors[key_part] = value_part
    return theme_colors


def load_variable(entries: list, name: str) -> dict | None:
    for entry in entries:
        if entry["name"] == name:
            return entry
    return None


def build_buttons_component(theme_colors: OrderedDict, entries: list) -> list:
    hover_shade = load_variable(entries, "$btn-hover-bg-shade-amount")
    hover_tint = load_variable(entries, "$btn-hover-bg-tint-amount")
    hover_border_shade = load_variable(entries, "$btn-hover-border-shade-amount")
    hover_border_tint = load_variable(entries, "$btn-hover-border-tint-amount")
    active_shade = load_variable(entries, "$btn-active-bg-shade-amount")
    active_tint = load_variable(entries, "$btn-active-bg-tint-amount")
    active_border_shade = load_variable(entries, "$btn-active-border-shade-amount")
    active_border_tint = load_variable(entries, "$btn-active-border-tint-amount")

    results = []
    for variant in theme_colors.keys():
        variant_entry = {
            "variant": variant,
            "vars": OrderedDict(),
            "layer": "bootstrap-core",
            "mode": "any",
            "notes": "Generated via mixins/_buttons.scss button-variant"
        }
        base = variant
        variant_entry["vars"]["--bs-btn-bg"] = f"alias: {base}"
        variant_entry["vars"]["--bs-btn-color"] = f"contrast({base})"
        variant_entry["vars"]["--bs-btn-border-color"] = f"alias: {base}"
        hover_formula = (
            f"shade({base}, {hover_shade['value_raw']}) / tint({base}, {hover_tint['value_raw']})"
            if hover_shade and hover_tint
            else f"shade({base}, 15%) / tint({base}, 15%)"
        )
        variant_entry["vars"]["--bs-btn-hover-bg"] = hover_formula
        hover_border_formula = (
            f"shade({base}, {hover_border_shade['value_raw']}) / tint({base}, {hover_border_tint['value_raw']})"
            if hover_border_shade and hover_border_tint
            else f"shade({base}, 20%) / tint({base}, 10%)"
        )
        variant_entry["vars"]["--bs-btn-hover-border-color"] = hover_border_formula
        active_formula = (
            f"shade({base}, {active_shade['value_raw']}) / tint({base}, {active_tint['value_raw']})"
            if active_shade and active_tint
            else f"shade({base}, 20%) / tint({base}, 20%)"
        )
        variant_entry["vars"]["--bs-btn-active-bg"] = active_formula
        active_border_formula = (
            f"shade({base}, {active_border_shade['value_raw']}) / tint({base}, {active_border_tint['value_raw']})"
            if active_border_shade and active_border_tint
            else f"shade({base}, 25%) / tint({base}, 10%)"
        )
        variant_entry["vars"]["--bs-btn-active-border-color"] = active_border_formula
        variant_entry["vars"]["--bs-btn-focus-shadow-rgb"] = f"mix(contrast({base}), {base}, 15%)"
        variant_entry["vars"]["--bs-btn-active-color"] = f"contrast({base})"
        variant_entry["vars"]["--bs-btn-disabled-bg"] = f"alias: {base}"
        variant_entry["vars"]["--bs-btn-disabled-border-color"] = f"alias: {base}"
        variant_entry["vars"]["--bs-btn-disabled-color"] = f"contrast({base})"
        results.append(variant_entry)
    return results


def build_alerts_component(theme_colors: OrderedDict) -> list:
    results = []
    for variant in theme_colors.keys():
        block = {
            "variant": variant,
            "vars": OrderedDict(),
            "layer": "bootstrap-core",
            "mode": "any",
            "notes": "Based on _alert.scss contextual modifiers"
        }
        block["vars"]["--bs-alert-color"] = f"alias: {variant}-text-emphasis"
        block["vars"]["--bs-alert-bg"] = f"alias: {variant}-bg-subtle"
        block["vars"]["--bs-alert-border-color"] = f"alias: {variant}-border-subtle"
        block["vars"]["--bs-alert-link-color"] = f"alias: {variant}-text-emphasis"
        results.append(block)
    return results


def build_badges_component(theme_colors: OrderedDict) -> list:
    results = []
    for variant in theme_colors.keys():
        block = {
            "variant": variant,
            "vars": OrderedDict(),
            "layer": "bootstrap-core",
            "mode": "any",
            "notes": "Derived from helpers/_color-bg.scss .text-bg variants"
        }
        block["vars"]["--bs-badge-color"] = f"contrast({variant})"
        block["vars"]["--bs-badge-bg"] = f"alpha({variant}, var(--bs-bg-opacity, 1))"
        block["vars"]["text-decoration-color"] = f"alpha({variant}, var(--bs-link-underline-opacity, 1))"
        results.append(block)
    return results


def build_links_component(theme_colors: OrderedDict, entries: list) -> list:
    link_shade = load_variable(entries, "$link-shade-percentage")
    shade_amount = link_shade["value_raw"] if link_shade else "0%"
    results = []
    for variant in theme_colors.keys():
        block = {
            "variant": variant,
            "vars": OrderedDict(),
            "layer": "bootstrap-core",
            "mode": "any",
            "notes": "helpers/_colored-links.scss link utilities"
        }
        block["vars"]["color"] = f"alpha({variant}, var(--bs-link-opacity, 1))"
        block["vars"]["text-decoration-color"] = f"alpha({variant}, var(--bs-link-underline-opacity, 1))"
        if shade_amount != "0%":
            block["vars"]["hover-color"] = (
                f"shade({variant}, {shade_amount}) / tint({variant}, {shade_amount})"
            )
        results.append(block)
    return results


def export_master(entries: list, out_dir: str):
    master_path = os.path.join(out_dir, "master_color_variables.json")
    with open(master_path, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2)


def export_css_vars(entries: list, out_dir: str):
    css_entries = [e for e in entries if e["type"] == "css-var"]
    path = os.path.join(out_dir, "css_vars_by_mode.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["css_var", "mode", "layer", "source_file", "derivation", "depends_on", "alpha_only"])
        for entry in css_entries:
            writer.writerow([
                entry["name"],
                entry["mode"],
                entry["layer"],
                entry["source_file"],
                entry.get("derivation", ""),
                "|".join(entry.get("depends_on", [])),
                str(entry.get("alpha_only", False)),
            ])


def export_component(path: str, data: list):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def build_figma_export(entries: list, theme_colors: OrderedDict) -> dict:
    collections = OrderedDict()
    hover_shade = load_variable(entries, "$btn-hover-bg-shade-amount")
    hover_tint = load_variable(entries, "$btn-hover-bg-tint-amount")
    hover_shade_val = hover_shade["value_raw"] if hover_shade else "15%"
    hover_tint_val = hover_tint["value_raw"] if hover_tint else "15%"
    theme_collection = {
        "modes": ["light", "dark"],
        "variables": OrderedDict(),
    }
    for color in theme_colors.keys():
        theme_collection["variables"][color] = {
            "type": "color",
            "valuesByMode": {"light": "alias", "dark": "alias"},
            "alias": None,
            "derivation": "base",
            "alpha_only": False,
        }
        theme_collection["variables"][f"{color}-bg-subtle"] = {
            "type": "color",
            "valuesByMode": {"light": "alias", "dark": "alias"},
            "alias": color,
            "derivation": f"subtle({color})",
            "alpha_only": False,
        }
        theme_collection["variables"][f"btn[{color}]-bg"] = {
            "type": "color",
            "valuesByMode": {"light": "alias", "dark": "alias"},
            "alias": color,
            "derivation": "alias",
            "alpha_only": False,
        }
        theme_collection["variables"][f"btn[{color}]-hover-bg"] = {
            "type": "color",
            "valuesByMode": {"light": "derived", "dark": "derived"},
            "alias": None,
            "derivation": f"shade({color}, {hover_shade_val}) / tint({color}, {hover_tint_val})",
            "alpha_only": False,
        }
    link_color_entry = next((e for e in entries if e["name"] == "$link-color"), None)
    link_hover_entry = next((e for e in entries if e["name"] == "$link-hover-color"), None)
    theme_collection["variables"]["link-color"] = {
        "type": "color",
        "valuesByMode": {"light": "derived", "dark": "derived"},
        "alias": None,
        "derivation": link_color_entry["derivation"] if link_color_entry else "shift(primary, variable)",
        "alpha_only": False,
    }
    theme_collection["variables"]["link-hover-color"] = {
        "type": "color",
        "valuesByMode": {"light": "derived", "dark": "derived"},
        "alias": None,
        "derivation": link_hover_entry["derivation"] if link_hover_entry else "shift(primary, variable)",
        "alpha_only": False,
    }
    collections["Theme"] = theme_collection

    palette_collection = {
        "modes": ["light", "dark"],
        "variables": OrderedDict(),
    }
    for entry in entries:
        if entry["semantic_group"] == "palette" and entry["type"] != "css-var":
            base_name = entry["name"].lstrip("$")
            palette_collection["variables"][base_name] = {
                "type": "color",
                "valuesByMode": {"light": "alias", "dark": "alias"},
                "alias": None,
                "derivation": "palette",
                "alpha_only": False,
            }
    collections["Palette"] = palette_collection

    return {"collections": collections}


def export_figma(entries: list, theme_colors: OrderedDict, out_dir: str):
    path = os.path.join(out_dir, "figma_variables.json")
    data = build_figma_export(entries, theme_colors)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def export_report(entries: list, out_dir: str):
    path = os.path.join(out_dir, "report.md")
    total = len(entries)
    css_total = sum(1 for e in entries if e["type"] == "css-var")
    scss_total = total - css_total
    layers = defaultdict(int)
    for entry in entries:
        layers[entry["layer"]] += 1
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Color Token Extraction\n\n")
        f.write(f"* Total tokens: {total}\n")
        f.write(f"* CSS variables: {css_total}\n")
        f.write(f"* SCSS variables & maps: {scss_total}\n")
        f.write("* Layer distribution:\n")
        for layer, count in layers.items():
            f.write(f"  * {layer}: {count}\n")


def main():
    all_files = []
    for base in TARGET_PATHS:
        for root, _, files in os.walk(base):
            for file in files:
                if file.endswith(".scss"):
                    all_files.append(os.path.join(root, file))
    for file in EXTRA_FILES:
        if os.path.exists(file):
            all_files.append(file)

    entries = []
    for path in sorted(all_files):
        entries.extend(parse_scss_variables(path))

    css_entries = []
    for path in sorted(all_files):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        mode_map = determine_mode_map(text)
        css_entries.extend(parse_css_variables(path, mode_map))

    entries.extend(css_entries)
    entries = enrich_entries(entries)

    out_dir = ensure_out_paths()
    theme_colors = parse_theme_colors(entries)
    export_master(entries, out_dir)
    export_css_vars(entries, out_dir)

    buttons = build_buttons_component(theme_colors, entries)
    alerts = build_alerts_component(theme_colors)
    badges = build_badges_component(theme_colors)
    links = build_links_component(theme_colors, entries)

    export_component(os.path.join(out_dir, "components", "buttons.json"), buttons)
    export_component(os.path.join(out_dir, "components", "alerts.json"), alerts)
    export_component(os.path.join(out_dir, "components", "badges.json"), badges)
    export_component(os.path.join(out_dir, "components", "links.json"), links)

    export_figma(entries, theme_colors, out_dir)
    export_report(entries, out_dir)


if __name__ == "__main__":
    main()
