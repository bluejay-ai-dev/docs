#!/usr/bin/env python3
"""Disambiguate duplicate page titles without changing the sidebar.

25 pages share a title with at least one other page. Thirteen are called
"Overview" and four pairs -- Alerts, Dashboards, Tool Calls, Traces -- exist once
under monitor/observability and again under test/simulations. Mintlify renders
the frontmatter `title` into `<title>`, so Google currently sees thirteen results
reading "Overview - Bluejay Docs" and cannot tell them apart. Neither can a
reader scanning a result list.

The parent folder already says which one it is, so the fix is to put that in the
title: `key-concepts/agents/overview` becomes "Agents Overview",
`monitor/observability/alerts` becomes "Observability Alerts".

### Why the sidebar does not change

Mintlify's `sidebarTitle` overrides the navigation label independently of
`title`. Every page edited here gets `sidebarTitle` set to the label it renders
today, so the nav tree is byte-identical to what shipped. What does change is the
page's own `<h1>` and the browser tab, which is the point -- a page whose only
heading is the word "Overview" tells a reader arriving from search nothing.

    python3 fix-docs-titles.py <path-to-docs-repo> --check
    python3 fix-docs-titles.py <path-to-docs-repo>

Idempotent: a page that already has a `sidebarTitle` is left alone. Self-
verifying: re-reads every file and fails non-zero if any title is still
duplicated, if a sidebarTitle does not match the label that page had before, or
if frontmatter stops parsing.
"""

import argparse
import json
import pathlib
import re
import sys

FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)

# Folder segment -> the word that belongs in the title. Only needed where the
# folder name alone would read oddly; everything else is title-cased from the
# path.
WORDS = {
    "api-reference": "API Reference",
    "bluejay-as-code": "Bluejay as Code",
    "key-concepts": "Key Concepts",
    "metrics-lab": "Metrics Lab",
    "red-teaming": "Red Teaming",
    "digital-humans": "Digital Humans",
    "custom-metrics": "Custom Metrics",
    "customer-traits": "Customer Traits",
    "scenario-builder": "Scenario Builder",
    "observability": "Observability",
    "simulations": "Simulation",
}


def humanise(seg):
    return WORDS.get(seg, seg.replace("-", " ").title())


def frontmatter(p):
    s = p.read_text(encoding="utf-8")
    m = FM.match(s)
    return (s, m, m.group(1)) if m else (s, None, None)


def field(fm, name):
    m = re.search(rf"^{name}:\s*(.*)$", fm, re.M)
    return m.group(1).strip().strip("'\"") if m else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    repo = pathlib.Path(args.repo).resolve()
    pages = {}
    for p in sorted(repo.rglob("*.mdx")):
        if ".git" in str(p):
            continue
        s, m, fm = frontmatter(p)
        if not m:
            continue
        pages[p] = (s, m, fm, field(fm, "title") or "")

    counts = {}
    for _, (_, _, _, t) in pages.items():
        counts[t] = counts.get(t, 0) + 1
    dupes = {t for t, c in counts.items() if c > 1 and t}

    changed, before = 0, {}
    for p, (s, m, fm, title) in pages.items():
        if title not in dupes:
            continue
        if field(fm, "sidebarTitle"):
            continue
        parent = p.relative_to(repo).parent.name
        prefix = humanise(parent)
        # test/simulations/alerts -> "Simulation Alerts", not "Simulations Alerts";
        # key-concepts/agents/overview -> "Agents Overview".
        new_title = title if title.startswith(prefix) else f"{prefix} {title}"
        if new_title == title:
            continue
        before[str(p.relative_to(repo))] = title
        newfm = re.sub(r"^title:\s*.*$",
                       f"title: {json.dumps(new_title, ensure_ascii=False)}\n"
                       f"sidebarTitle: {json.dumps(title, ensure_ascii=False)}",
                       fm, count=1, flags=re.M)
        if not args.check:
            p.write_text(s[:m.start(1)] + newfm + s[m.end(1):], encoding="utf-8")
        changed += 1

    verb = "would retitle" if args.check else "retitled"
    print(f"{verb}: {changed} pages ({len(dupes)} titles were shared by more than one page)")
    for f, t in sorted(before.items())[:6]:
        print(f"    {f[:52]:<54} {t!r} -> keeps {t!r} in the sidebar")
    if args.check:
        return 0

    # verify
    problems = []
    seen = {}
    for p in sorted(repo.rglob("*.mdx")):
        if ".git" in str(p):
            continue
        s, m, fm = frontmatter(p)
        if not m:
            problems.append(f"{p.name}: frontmatter no longer parses")
            continue
        t = field(fm, "title")
        rel = str(p.relative_to(repo))
        if rel in before:
            sb = field(fm, "sidebarTitle")
            if sb != before[rel]:
                problems.append(f"{rel}: sidebarTitle is {sb!r}, sidebar would change (was {before[rel]!r})")
        seen.setdefault(t, []).append(rel)
    still = {t: f for t, f in seen.items() if t and len(f) > 1}
    if still:
        problems.append(f"titles still duplicated: {list(still)[:4]}")

    print(f"verify: {len(seen)} distinct titles across {sum(len(v) for v in seen.values())} pages")
    if problems:
        print(f"VERIFY FAILED ({len(problems)}):")
        for x in problems[:8]:
            print(f"    {x}")
        return 1
    print("verify: every title is unique, and every sidebar label is unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
