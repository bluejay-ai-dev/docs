#!/usr/bin/env python3
"""Redirect the renamed docs URLs and give the API reference real descriptions.

Two things Search Console surfaced on docs.getbluejay.ai:

1. **106 URLs Google still crawls return 404.** The API reference was
   restructured -- endpoints moved from `/v1/<name>` and
   `/api-reference/<group>/<name>` to `/api-reference/endpoint/<name>` -- and a
   handful of guide pages moved too (`/monitor/overview` ->
   `/monitor/observability/overview`). docs.json already carries 47 redirects,
   so this appends to an established list.

   48 of the 106 map to a live page by an exact last-segment match, plus six
   guide pages checked by hand against the folder listing. The remaining 58 are
   left alone on purpose: 16 are route patterns containing `{param}` or `:slug*`
   rather than URLs, and 41 name endpoints that no longer exist under any name.
   Pointing those at the API reference index would be a soft 404, which Google
   treats worse than the honest 404 they return today.

2. **87 of the 105 API reference pages have no meta description** -- four have
   no key at all and 83 have `description: ''`. These pages rank (several
   between positions 3 and 7), so Google is writing their search snippets from
   whatever it can scrape off a page whose body is mostly a code sample.

   The descriptions are not invented here. Every page carries an authoritative
   one-liner in its body -- `> **What this endpoint does:** ...` -- written by
   whoever documented the endpoint. 74 pages have one and it is lifted verbatim,
   trimmed to a whole sentence within a snippet-sized limit. The 13 without one
   are left for someone who knows the endpoint.

    python3 fix-docs-seo.py <path-to-docs-repo> --check
    python3 fix-docs-seo.py <path-to-docs-repo>

Idempotent: existing redirects are not duplicated and a page that already has a
non-empty description is skipped. Self-verifying: re-reads docs.json and every
page it touched, and fails non-zero on a duplicate redirect source, a redirect
whose destination is not a real page, or frontmatter that no longer parses.
"""

import argparse
import json
import pathlib
import re
import sys

# Google truncates a snippet around 155-160 characters, so anything past this is
# invisible in results and only dilutes the useful part.
DESC_MAX = 155
WHAT = re.compile(r"\*\*What this (?:endpoint|webhook) does:\*\*\s*(.+)")
FM = re.compile(r"\A---\n(.*?)\n---\n", re.S)

# Several source lines are raw docstrings that continue into implementation
# detail -- "Args: test_result_id: the ID of...", "Returns: the test result...",
# status-code branches like "- if label is missing -> 400". None of that belongs
# in a search snippet, so the description stops where the prose does.
TAIL = re.compile(r"\s+(?:Args:|Returns:|Raises:|Params:|Note:|-\s|->)", re.I)

# Guide pages, each checked against the repo's folder listing rather than
# matched by string similarity -- "overview" appears under several folders.
MANUAL = {
    "/monitor/overview": "/monitor/observability/overview",
    "/test/overview": "/test/simulations/overview",
    "/cookbook/observability": "/monitor/observability/overview",
    "/bluejay-as-code": "/key-concepts/bluejay-as-code/overview",
    "/v1/bluejay-as-code": "/key-concepts/bluejay-as-code/overview",
    "/key-concepts/bluejay-as-code/skill.txt": "/key-concepts/bluejay-as-code/skill",
}


def page_paths(repo):
    return {"/" + str(p.relative_to(repo)).replace(".mdx", ""): p
            for p in repo.rglob("*.mdx") if ".git" not in str(p)}


def snippet(text, limit=DESC_MAX):
    """A source line turned into something that reads well in a search result."""
    text = re.sub(r"\s+", " ", text).strip()
    cut = TAIL.search(text)
    if cut:
        text = text[:cut.start()].strip()
    # Markdown survives into the snippet as literal asterisks and backticks.
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = text.strip().strip("*").strip()
    if len(text) > limit:
        parts = re.findall(r"[^.!?]+[.!?]+(?:\s|$)", text)
        out = ""
        for s in parts:
            if out and len(out) + len(s) > limit:
                break
            out += s
        text = (out or text[:limit].rsplit(" ", 1)[0]).strip()
    if not text:
        return ""
    # Many source lines start lower-case ("delete a specific prompt version");
    # a snippet that opens mid-sentence reads as broken.
    text = text[0].upper() + text[1:]
    if not text.endswith((".", "!", "?")):
        text += "."
    return text


def build_redirects(repo, dead_file, pages, existing):
    by_last = {}
    for path in pages:
        by_last.setdefault(path.rsplit("/", 1)[-1], []).append(path)
    new, skipped = [], []
    for line in pathlib.Path(dead_file).read_text().split("\n"):
        d = line.strip()
        if not d or d in existing:
            continue
        if d in MANUAL:
            new.append({"source": d, "destination": MANUAL[d]})
            continue
        if "{" in d or ":slug" in d:
            skipped.append((d, "route pattern, not a URL"))
            continue
        hits = by_last.get(d.rsplit("/", 1)[-1], [])
        if len(hits) == 1:
            new.append({"source": d, "destination": hits[0]})
        else:
            skipped.append((d, "no page with that name" if not hits else f"ambiguous ({len(hits)})"))
    return new, skipped


def fill_descriptions(pages, apply):
    filled, no_source = 0, []
    touched = []
    for path, p in sorted(pages.items()):
        s = p.read_text(encoding="utf-8")
        m = FM.match(s)
        if not m:
            continue
        fm = m.group(1)
        cur = re.search(r"^description:\s*(.*)$", fm, re.M)
        if cur and cur.group(1).strip().strip("'\""):
            continue
        w = WHAT.search(s)
        if not w:
            no_source.append(path)
            continue
        desc = snippet(w.group(1))
        if not desc:
            no_source.append(path)
            continue
        # json.dumps gives a double-quoted, correctly escaped scalar. Several of
        # these lines contain an apostrophe, which would end a single-quoted YAML
        # value early and leave the frontmatter unparseable.
        line = f"description: {json.dumps(desc, ensure_ascii=False)}"
        newfm = (re.sub(r"^description:\s*.*$", line, fm, count=1, flags=re.M)
                 if cur else re.sub(r"^(title:\s*.*)$", r"\1\n" + line, fm, count=1, flags=re.M))
        if apply:
            p.write_text(s[:m.start(1)] + newfm + s[m.end(1):], encoding="utf-8")
        filled += 1
        touched.append(p)
    return filled, no_source, touched


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repo")
    ap.add_argument("--dead", default=None, help="file of 404 paths, one per line")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    repo = pathlib.Path(args.repo).resolve()
    cfg = repo / "docs.json"
    if not cfg.exists():
        sys.exit(f"no docs.json under {repo}")
    doc = json.loads(cfg.read_text(encoding="utf-8"))
    pages = page_paths(repo)
    existing = {r["source"] for r in doc.get("redirects", [])}

    new = []
    skipped = []
    if args.dead:
        new, skipped = build_redirects(repo, args.dead, pages, existing)

    filled, no_source, touched = fill_descriptions(pages, apply=not args.check)

    verb = "would add" if args.check else "added"
    print(f"{verb}: {len(new)} redirects (docs.json had {len(existing)})")
    print(f"{verb.replace('add','fill')}: {filled} descriptions lifted from each page's own body")
    if skipped:
        print(f"left 404ing on purpose: {len(skipped)}")
    if no_source:
        print(f"no 'What this endpoint does' line, left alone: {len(no_source)}")

    if args.check:
        return 0

    if new:
        doc.setdefault("redirects", []).extend(new)
        cfg.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # verify
    doc2 = json.loads(cfg.read_text(encoding="utf-8"))
    problems = []
    srcs = [r["source"] for r in doc2["redirects"]]
    if len(srcs) != len(set(srcs)):
        dupes = {s for s in srcs if srcs.count(s) > 1}
        problems.append(f"duplicate redirect sources: {sorted(dupes)[:4]}")
    for r in doc2["redirects"]:
        d = r["destination"]
        if "{" in d or ":slug" in d or d.startswith("http"):
            continue
        if d not in pages:
            problems.append(f"redirect target is not a page: {r['source']} -> {d}")
    for p in touched:
        s = p.read_text(encoding="utf-8")
        m = FM.match(s)
        if not m:
            problems.append(f"{p.name}: frontmatter no longer parses")
            continue
        d = re.search(r"^description:\s*(.*)$", m.group(1), re.M)
        if not d or not d.group(1).strip().strip("'\""):
            problems.append(f"{p.name}: description still empty")

    print(f"verify: {len(doc2['redirects'])} redirects and {len(touched)} pages checked")
    if problems:
        print(f"VERIFY FAILED ({len(problems)}):")
        for x in problems[:8]:
            print(f"    {x}")
        return 1
    print("verify: no duplicate sources, every target resolves, all frontmatter parses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
