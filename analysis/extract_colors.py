import os
import re
import json
from collections import defaultdict

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(ROOT_DIR, os.pardir))
SCSS_BASE = os.path.join(REPO_ROOT, "src", "scss")

COLOR_FUNCS = {
    "tint-color",
    "shade-color",
    "shift-color",
    "color-contrast",
    "mix",
    "rgba",
    "rgb",
    "hsla",
    "hsl",
    "alpha",
    "adjust-color",
    "adjust-hue",
    "darken",
    "lighten",
    "saturate",
    "desaturate",
    "fade-in",
    "fade-out",
}

THEME_KEYS = [
    "primary",
    "secondary",
    "success",
    "warning",
    "danger",
    "info",
    "light",
    "dark",
]

STATE_KEYS = [
    "hover",
    "active",
    "focus",
    "disabled",
    "visited",
    "checked",
    "indeterminate",
    "emphasis",
    "subtle",
    "pressed",
    "expanded",
    "selected",
]

SURFACE_KEYS = [
    "surface",
    "background",
    "bg",
    "body",
    "overlay",
    "panel",
]

TEXT_KEYS = ["text", "font", "copy"]
BORDER_KEYS = ["border", "outline", "divider", "stroke"]
LINK_KEYS = ["link", "anchor"]

PALETTE_PREFIXES = [
    "amber",
    "blue",
    "blue-grey",
    "brown",
    "cyan",
    "deep-orange",
    "deep-purple",
    "green",
    "grey",
    "indigo",
    "light-blue",
    "light-green",
    "lime",
    "orange",
    "pink",
    "purple",
    "red",
    "teal",
    "yellow",
]

HEX_RE = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
CSS_VAR_RE = re.compile(r"(--(?:bs|mdb)-[\w-]+)\s*:\s*([^;]+);")


def strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    cleaned_lines = []
    for line in text.splitlines():
        new_line = []
        in_single = False
        in_double = False
        i = 0
        while i < len(line):
            ch = line[i]
            if ch == "'" and not in_double:
                in_single = not in_single
                new_line.append(ch)
                i += 1
                continue
            if ch == '"' and not in_single:
                in_double = not in_double
                new_line.append(ch)
                i += 1
                continue
            if (
                ch == "/"
                and i + 1 < len(line)
                and line[i + 1] == "/"
                and not in_single
                and not in_double
            ):
                break
            new_line.append(ch)
            i += 1
        cleaned_lines.append("".join(new_line))
    return "\n".join(cleaned_lines)


def detect_layer(rel_path: str) -> str:
    if "src/scss/bootstrap" in rel_path:
        return "bootstrap-core"
    if "/bootstrap/" in rel_path:
        return "bootstrap-core"
    if "/free/" in rel_path:
        return "mdb-free"
    if "/custom/" in rel_path:
        return "custom"
    return "core"


LAYER_PRIORITY = {
    "bootstrap-core": 0,
    "core": 0,
    "mdb-free": 1,
    "mdb-pro": 1,
    "custom": 2,
}


def categorize(name: str, value: str) -> list[str]:
    categories: list[str] = []
    lower_name = name.lower()
    lower_value = value.lower() if value else ""
    for key in THEME_KEYS:
        if key in lower_name:
            categories.append(f"semantic:{key}")
    for prefix in PALETTE_PREFIXES:
        if prefix in lower_name:
            categories.append(f"palette:{prefix}")
    for key in SURFACE_KEYS:
        if re.search(rf"\b{re.escape(key)}\b", lower_name):
            categories.append(f"surface:{key}")
    for key in TEXT_KEYS:
        if re.search(rf"\b{re.escape(key)}\b", lower_name):
            categories.append(f"text:{key}")
    for key in BORDER_KEYS:
        if re.search(rf"\b{re.escape(key)}\b", lower_name):
            categories.append(f"border:{key}")
    for key in LINK_KEYS:
        if re.search(rf"\b{re.escape(key)}\b", lower_name):
            categories.append(f"link:{key}")
    for key in STATE_KEYS:
        if key in lower_name:
            categories.append(f"state:{key}")
    if not categories and lower_value:
        for key in THEME_KEYS:
            if key in lower_value:
                categories.append(f"semantic:{key}")
        for prefix in PALETTE_PREFIXES:
            if prefix in lower_value:
                categories.append(f"palette:{prefix}")
    if not categories:
        categories.append("uncategorized")
    return sorted(set(categories))


def detect_functions(value: str) -> list[str]:
    functions = []
    for func in sorted(COLOR_FUNCS):
        if func in value:
            functions.append(func)
    return functions


def extract_dependencies(value: str) -> list[str]:
    deps = set()
    for match in re.findall(r"\$([\w-]+)", value):
        deps.add(f"${match}")
    for match in re.findall(r"var\((--[\w-]+)", value):
        deps.add(match)
    for match in re.findall(r"--(?:bs|mdb)-[\w-]+", value):
        if match.startswith("--"):
            deps.add(match)
    return sorted(deps)


def resolve_value(raw_value: str) -> str | None:
    value = raw_value.strip()
    value = re.sub(r"\s*!default", "", value)
    value = re.sub(r"\s*!important", "", value)
    if HEX_RE.match(value):
        return value
    return None


def normalize_value(raw_value: str) -> str:
    return re.sub(r"\s+", " ", raw_value.strip())


def get_selector_before(text: str, idx: int) -> str:
    j = idx - 1
    while j >= 0 and text[j].isspace():
        j -= 1
    end = j
    while j >= 0 and text[j] not in "{};":
        j -= 1
    selector = text[j + 1 : end + 1].strip()
    return selector


def build_context_segments(text: str):
    segments = []
    stack: list[str] = []
    last = 0
    for match in re.finditer(r"[{}]", text):
        idx = match.start()
        if last < idx:
            segments.append((last, idx, tuple(stack)))
        if match.group() == "{":
            selector = get_selector_before(text, idx)
            if not selector:
                selector = "<anonymous>"
            stack.append(selector)
        else:
            if stack:
                stack.pop()
        last = idx + 1
    if last < len(text):
        segments.append((last, len(text), tuple(stack)))
    return segments


def context_at(segments, pos: int):
    for start, end, ctx in segments:
        if start <= pos < end:
            return ctx
    return ()


def detect_mode_from_context(context_stack) -> str:
    for ctx in reversed(context_stack):
        if "data-bs-theme" in ctx:
            if "dark" in ctx:
                return "dark"
            if "light" in ctx:
                return "light"
        if ctx.strip() == ":root":
            return "any"
    return "any"


def parse_scss_file(path: str):
    rel_path = os.path.relpath(path, REPO_ROOT)
    layer = detect_layer(rel_path)
    with open(path, "r", encoding="utf-8") as f:
        raw_text = f.read()
    text = strip_comments(raw_text)

    records = []
    map_names = set()

    map_pattern = re.compile(r"\$([\w-]+)\s*:\s*\((.*?)\)\s*(?:!default)?;", re.DOTALL)
    for match in map_pattern.finditer(text):
        name = match.group(1)
        map_body = match.group(2).strip()
        map_names.add(name)
        raw_value = "(" + map_body + ")"
        categories = categorize(name, raw_value)
        deps = extract_dependencies(raw_value)
        functions = detect_functions(raw_value)
        notes = []
        if functions:
            notes.append("functions: " + ", ".join(functions))
        entries = [line.strip() for line in map_body.splitlines() if ":" in line]
        if entries:
            notes.append(f"entries: {len(entries)}")
        records.append(
            {
                "name": f"${name}",
                "type": "scss-map",
                "semantic_group": categories,
                "mode": "any",
                "source_file": rel_path,
                "value_raw": raw_value,
                "value_resolved": None,
                "derivation": raw_value,
                "depends_on": deps,
                "layer": layer,
                "notes": notes,
                "functions": functions,
            }
        )

    var_pattern = re.compile(r"\$([\w-]+)\s*:\s*([^;]+);")
    for match in var_pattern.finditer(text):
        name = match.group(1)
        if name in map_names:
            continue
        raw_value = match.group(2).strip()
        categories = categorize(name, raw_value)
        deps = extract_dependencies(raw_value)
        functions = detect_functions(raw_value)
        notes = []
        if functions:
            notes.append("functions: " + ", ".join(functions))
        clean_value = normalize_value(raw_value)
        resolved = resolve_value(raw_value)
        records.append(
            {
                "name": f"${name}",
                "type": "scss-var",
                "semantic_group": categories,
                "mode": "any",
                "source_file": rel_path,
                "value_raw": raw_value,
                "value_resolved": resolved,
                "derivation": clean_value,
                "depends_on": deps,
                "layer": layer,
                "notes": notes,
                "functions": functions,
            }
        )

    segments = build_context_segments(raw_text)
    for match in CSS_VAR_RE.finditer(raw_text):
        name = match.group(1)
        raw_value = match.group(2).strip()
        context_stack = context_at(segments, match.start())
        mode = detect_mode_from_context(context_stack)
        categories = categorize(name, raw_value)
        deps = extract_dependencies(raw_value)
        functions = detect_functions(raw_value)
        notes = []
        if functions:
            notes.append("functions: " + ", ".join(functions))
        if context_stack:
            notes.append("context: " + " > ".join(context_stack))
        resolved = resolve_value(raw_value)
        records.append(
            {
                "name": name,
                "type": "css-var",
                "semantic_group": categories,
                "mode": mode,
                "source_file": rel_path,
                "value_raw": raw_value,
                "value_resolved": resolved,
                "derivation": normalize_value(raw_value),
                "depends_on": deps,
                "layer": layer,
                "notes": notes,
                "functions": functions,
            }
        )

    return records


def build_summary(records: list[dict], overrides: list[dict]) -> str:
    theme_summary = defaultdict(list)
    palette_summary = defaultdict(list)
    state_records = defaultdict(list)
    for record in records:
        for category in record["semantic_group"]:
            if category.startswith("semantic:"):
                theme_summary[category.split(":", 1)[1]].append(record)
            if category.startswith("palette:"):
                palette_summary[category.split(":", 1)[1]].append(record)
            if category.startswith("state:"):
                state_records[category.split(":", 1)[1]].append(record)
    lines = ["# Farb-Analyse Report", ""]
    lines.append("## Theme-Farben & Paletten")
    lines.append("")
    if theme_summary:
        lines.append("### Theme-Farben")
        for key, recs in sorted(theme_summary.items()):
            layers = sorted(set(r["layer"] for r in recs))
            lines.append(f"- **{key}** ({len(recs)} Vorkommen) – Layer: {', '.join(layers)}")
    if palette_summary:
        lines.append("")
        lines.append("### Palettenfarben")
        for key, recs in sorted(palette_summary.items()):
            lines.append(f"- **{key}** ({len(recs)} Tokens)")
    lines.append("")
    lines.append("## Berechnungsregeln für States")
    lines.append("")
    if state_records:
        for state, recs in sorted(state_records.items()):
            functions = sorted({func for r in recs for func in r.get("functions", []) if func})
            samples = [f"{r['name']} ({r['layer']})" for r in recs[:5]]
            sample_text = ", ".join(samples)
            if len(recs) > 5:
                sample_text += f" … (+{len(recs) - 5} weitere)"
            func_text = ", ".join(functions) if functions else "keine Farb-Funktionen"
            lines.append(f"- **{state}** ({len(recs)} Tokens) – Funktionen: {func_text}; Beispiele: {sample_text}")
    else:
        lines.append("- Keine expliziten State-Ableitungen identifiziert.")
    lines.append("")
    lines.append("## Wichtigste Overrides")
    lines.append("")
    if overrides:
        max_items = 20
        for item in overrides[:max_items]:
            lines.append(
                f"- {item['name']} ({item['type']}) in {item['override_file']} überschreibt {item['base_file']} [{item['layer']}]"
            )
        if len(overrides) > max_items:
            lines.append(f"- … {len(overrides) - max_items} weitere Overrides")
    else:
        lines.append("- Keine Overrides erkannt.")
    lines.append("")
    return "\n".join(lines)


def build_outputs():
    scss_files = []
    for root, _, files in os.walk(SCSS_BASE):
        for filename in files:
            if filename.endswith(".scss"):
                scss_files.append(os.path.join(root, filename))

    all_records = []
    for path in sorted(scss_files):
        all_records.extend(parse_scss_file(path))

    by_key: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for idx, record in enumerate(all_records):
        record["_index"] = idx
        by_key[(record["type"], record["name"])].append(record)

    overrides = []
    for key, recs in by_key.items():
        recs.sort(key=lambda r: (LAYER_PRIORITY.get(r["layer"], 99), r["_index"]))
        if recs:
            recs[0]["is_override"] = False
        for r in recs[1:]:
            r["is_override"] = True
            base = recs[0]
            r.setdefault("notes", []).append(
                f"overrides {base['name']} from {base['source_file']} ({base['layer']})"
            )
            overrides.append(
                {
                    "name": r["name"],
                    "type": r["type"],
                    "override_file": r["source_file"],
                    "base_file": base["source_file"],
                    "layer": r["layer"],
                }
            )

    overrides.sort(key=lambda item: (item["override_file"], item["name"]))

    for record in all_records:
        record.pop("_index", None)
        record.setdefault("is_override", False)

    all_records.sort(key=lambda r: (r["name"], r["type"], r["source_file"]))

    graph_nodes = {}
    graph_edges = []
    for record in all_records:
        node_id = f"{record['type']}::{record['name']}"
        if node_id not in graph_nodes:
            graph_nodes[node_id] = {
                "id": node_id,
                "name": record["name"],
                "type": record["type"],
                "layer": record["layer"],
            }
        for dep in record["depends_on"]:
            dep_type = "css-var" if dep.startswith("--") else "scss-var"
            graph_edges.append(
                {
                    "from": node_id,
                    "to": f"{dep_type}::{dep}",
                    "description": f"{record['name']} depends on {dep}",
                }
            )

    graph = {
        "nodes": list(graph_nodes.values()),
        "edges": graph_edges,
    }

    figma_vars: dict[str, dict] = {}
    mode_ids = {
        "any": "MODE_ANY",
        "light": "MODE_LIGHT",
        "dark": "MODE_DARK",
    }
    for record in all_records:
        if record["type"] == "scss-map":
            continue
        key = record["name"]
        entry = figma_vars.setdefault(
            key,
            {
                "name": key,
                "type": "COLOR",
                "valuesByMode": {},
            },
        )
        mode = record["mode"] if record["mode"] in mode_ids else "any"
        entry["valuesByMode"][mode_ids[mode]] = record["value_resolved"] or record["value_raw"]

    figma = {
        "collections": [
            {
                "name": "MDB Color Tokens",
                "modes": [
                    {"modeId": "MODE_ANY", "name": "Any"},
                    {"modeId": "MODE_LIGHT", "name": "Light"},
                    {"modeId": "MODE_DARK", "name": "Dark"},
                ],
                "variables": sorted(figma_vars.values(), key=lambda v: v["name"]),
            }
        ]
    }

    summary = build_summary(all_records, overrides)

    output_dir = ROOT_DIR
    with open(os.path.join(output_dir, "master_color_variables.json"), "w", encoding="utf-8") as f:
        json.dump(all_records, f, indent=2, ensure_ascii=False)
    with open(os.path.join(output_dir, "color_dependency_graph.json"), "w", encoding="utf-8") as f:
        json.dump(graph, f, indent=2, ensure_ascii=False)
    with open(os.path.join(output_dir, "figma_variables.json"), "w", encoding="utf-8") as f:
        json.dump(figma, f, indent=2, ensure_ascii=False)
    with open(os.path.join(output_dir, "color_report.md"), "w", encoding="utf-8") as f:
        f.write(summary)


if __name__ == "__main__":
    build_outputs()

