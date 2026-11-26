#!/usr/bin/env python3
"""Write the endpoint tables of site/pages/api-reference/cheat-sheet.mdx from the API nav in site/docs.json.

Each top-level nav group becomes a heading and each resource group one table. Method and
path come from each page's `api:` frontmatter. The one-line summary is the first sentence
of the page's hand-written text. The page's frontmatter and intro are kept.

Usage: python3 scripts/generate_cheat_sheet.py
"""

import json
import os
import re

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_DIR = os.path.join(DOCS_DIR, "site")
PAGES_DIR = os.path.join(SITE_DIR, "pages")
OUT = os.path.join(PAGES_DIR, "api-reference", "cheat-sheet.mdx")
GENERATED_MARK = "{/* GENERATED"
PRODUCT_NAME = re.compile(r"Digital Human|Scenario Builder|Red Teaming|Self-Improve|Metrics Lab|Knowledge Base")


def heading(group):
    """Nav groups are Title Case for the sidebar; headings are sentence case except product names."""
    if PRODUCT_NAME.search(group):
        return group
    first, _, rest = group.partition(" ")
    return f"{first} {rest.lower()}" if rest else first


def leaf(entry):
    """The page of a sidebar entry, or None when the entry is a group."""
    return entry if isinstance(entry, str) else entry.get("page")


def read_page(slug):
    text = open(os.path.join(PAGES_DIR, slug + ".mdx")).read()
    fm, body = text.split("---", 2)[1:]
    m = re.search(r'^api:\s*["\']?([A-Z]+) https?://[^/]+([^"\'\n]+)', fm, re.M)
    webhook = "/webhook/" in slug
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
    leaves = [leaf(p) for p in group["pages"] if leaf(p)]
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
        if leaf(p) is None and not p.get("hidden"):
            out += tables(p, depth + 1 if rows else depth)
    return out


def main():
    nav = json.load(open(os.path.join(SITE_DIR, "docs.json")))["navigation"]["tabs"]
    tab = next(t for t in nav if t["tab"] == "API")
    head = open(OUT).read().split("\n## ", 1)[0].rstrip() + "\n"
    out = [head]
    for top in tab["groups"]:
        if top.get("hidden"):
            continue
        sections = []
        for p in top["pages"]:
            if leaf(p) is None and not p.get("hidden"):
                sections += tables(p, 3)
        if sections:
            out.append(f"## {heading(top['group'])}\n")
            out += sections
    open(OUT, "w").write("\n".join(out))
    print(f"Wrote {sum(s.count('](/') for s in out)} endpoints to {OUT}")


if __name__ == "__main__":
    main()
