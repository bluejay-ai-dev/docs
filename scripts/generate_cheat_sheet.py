#!/usr/bin/env python3
"""Write api-reference/cheat-sheet.mdx from the API Reference nav in docs.json.

Each nav group becomes one table. Method and path come from each page's `openapi:`
frontmatter. The one-line summary is the first sentence of the page body.

Usage: python3 scripts/generate_cheat_sheet.py
"""

import json
import os
import re

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(DOCS_DIR, "api-reference", "cheat-sheet.mdx")

HEADER = """---
title: "API Cheat Sheet"
sidebarTitle: "Cheat Sheet"
description: "All Bluejay API endpoints on one page, grouped by resource, with the HTTP method, the path, and one line about what each endpoint does."
---

Every documented endpoint, grouped as in the sidebar. The base URL is `https://api.getbluejay.ai`. Select an endpoint to open its page.
"""


def read_page(slug):
    text = open(os.path.join(DOCS_DIR, slug + ".mdx")).read()
    fm, body = text.split("---", 2)[1:]
    m = re.search(r"^openapi:\s*['\"]?([A-Z]+) ([^'\"\n]+)", fm, re.M)
    if not m:
        return None
    body = re.sub(r'<div className="ai-prompt-box">.*?````\n</div>\n', "", body, flags=re.S)
    body = re.sub(r"<Warning>.*?</Warning>", "", body, flags=re.S)
    first = next((ln for ln in body.strip().split("\n") if ln.strip()), "")
    line = re.split(r"(?<=\.)\s", first.strip(), maxsplit=1)[0]
    line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line).replace("|", "\\|")
    deprecated = re.search(r"^deprecated:\s*true", fm, re.M) is not None
    if deprecated:
        line = "Deprecated. " + line
    return m.group(1), m.group(2).strip(), line


def walk(groups):
    for g in groups:
        pages = g.get("pages", [])
        leaves = [p for p in pages if isinstance(p, str)]
        if leaves and ("/endpoint/" in leaves[0] or "/webhook/" in leaves[0]):
            yield g["group"], leaves
        for p in pages:
            if isinstance(p, dict):
                yield from walk([p])


def main():
    nav = json.load(open(os.path.join(DOCS_DIR, "docs.json")))["navigation"]["tabs"]
    tab = next(t for t in nav if t["tab"] == "API Reference")
    out = [HEADER]
    count = 0
    for group, slugs in walk(tab["groups"]):
        rows = []
        for slug in slugs:
            page = read_page(slug)
            if not page:
                continue
            method, path, line = page
            if method == "WEBHOOK":
                path = "Your URL"
            rows.append(f"| `{method}` | [`{path}`](/{slug}) | {line} |")
        if not rows:
            continue
        count += len(rows)
        out.append(f"## {group}\n\n| Method | Path | Description |\n|---|---|---|\n" + "\n".join(rows) + "\n")
    open(OUT, "w").write("\n".join(out))
    print(f"Wrote {count} endpoints to {OUT}")


if __name__ == "__main__":
    main()
