#!/usr/bin/env python3
"""Write the endpoint tables of api-reference/cheat-sheet.mdx from the API nav in docs.json.

Each top-level nav group becomes a heading and each resource group one table. Method and
path come from each page's `api:` frontmatter. The one-line summary is the first sentence
of the page's hand-written text. The page's frontmatter and intro are kept.

Usage: python3 scripts/generate_cheat_sheet.py
"""

import json
import os
import re

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(DOCS_DIR, "api-reference", "cheat-sheet.mdx")
GENERATED_MARK = "{/* GENERATED"
IMPORT = 'import { Method } from "/snippets/method.jsx";'
PRODUCT_NAME = re.compile(r"Digital Human|Scenario Builder|Red Teaming|Self-Improve|Metrics Lab|Knowledge Base")


def heading(group):
    """Nav groups are Title Case for the sidebar; headings are sentence case except product names."""
    if PRODUCT_NAME.search(group):
        return group
    first, _, rest = group.partition(" ")
    return f"{first} {rest.lower()}" if rest else first


def read_page(slug):
    text = open(os.path.join(DOCS_DIR, slug + ".mdx")).read()
    fm, body = text.split("---", 2)[1:]
    m = re.search(r'^api:\s*["\']?([A-Z]+) https?://[^/]+([^"\'\n]+)', fm, re.M)
    webhook = re.search(r"^webhook:", fm, re.M)
    if not m and not webhook:
        return None
    method, path = (m.group(1), m.group(2).strip()) if m else ("WEBHOOK", "Your URL")
    body = body.split(GENERATED_MARK, 1)[0]
    lines = [ln for ln in body.strip().split("\n") if ln.strip() and not ln.startswith("import ")]
    lines = [ln for ln in lines if not ln.lstrip().startswith("<")]
    first = lines[0] if lines else ""
    if not first:
        desc = re.search(r'^description:\s*"?(.*?)"?$', fm, re.M)
        first = desc.group(1) if desc else ""
    line = re.split(r"(?<=\.)\s", first.strip(), maxsplit=1)[0]
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line).replace("|", "\\|")
    if re.search(r"^deprecated:\s*true", fm, re.M):
        line = "Deprecated. " + line
    return method, path, line


def tables(group, depth):
    out = []
    leaves = [p for p in group["pages"] if isinstance(p, str)]
    rows = []
    for slug in leaves:
        page = read_page(slug)
        if page:
            method, path, line = page
            pill = f"`{method}`" if method == "WEBHOOK" else f"<Method>{method}</Method>"
            rows.append(f"| {pill} | [`{path}`](/{slug}) | {line} |")
    if rows:
        out.append(f"{'#' * depth} {heading(group['group'])}\n\n| Method | Path | Description |\n|---|---|---|\n" + "\n".join(rows) + "\n")
    for p in group["pages"]:
        if isinstance(p, dict):
            out += tables(p, depth + 1 if rows else depth)
    return out


def main():
    nav = json.load(open(os.path.join(DOCS_DIR, "docs.json")))["navigation"]["tabs"]
    tab = next(t for t in nav if t["tab"] == "API")
    head = open(OUT).read().split("\n## ", 1)[0].rstrip() + "\n"
    if IMPORT not in head:
        fm_end = head.index("---", 3) + 3
        head = f"{head[:fm_end]}\n\n{IMPORT}{head[fm_end:]}"
    out = [head]
    for top in tab["groups"]:
        sections = []
        for p in top["pages"]:
            if isinstance(p, dict):
                sections += tables(p, 3)
        if sections:
            out.append(f"## {heading(top['group'])}\n")
            out += sections
    open(OUT, "w").write("\n".join(out))
    print(f"Wrote {sum(s.count('](/') for s in out)} endpoints to {OUT}")


if __name__ == "__main__":
    main()
