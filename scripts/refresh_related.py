"""Rewrite every <Related links={...}> block from the linked pages' frontmatter.

Each card shows the linked page's description and icon; an API endpoint page uses its
sidebar group's icon, and a link to a #section shows no description. Run after changing a
page's description or icon. --check reports pages that are out of date without writing.
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY = "--check" in sys.argv

docs = json.load(open(f"{ROOT}/docs.json"))
redirects = {r["source"]: r["destination"] for r in docs.get("redirects", [])}
group_icon = {}


def walk(n, icon=None):
    if isinstance(n, dict):
        icon = n.get("icon", icon) if "group" in n else icon
        for p in n.get("pages", []):
            if isinstance(p, str):
                group_icon.setdefault(p, icon)
            else:
                walk(p, icon)
        for k, v in n.items():
            if k != "pages":
                walk(v, icon)
    elif isinstance(n, list):
        for v in n:
            walk(v, icon)


walk(docs["navigation"])


def frontmatter(path):
    s = open(path).read()
    m = re.match(r"---\n(.*?)\n---\n", s, re.S)
    out = {}
    for line in (m.group(1) if m else "").splitlines():
        k, _, v = line.partition(":")
        v = v.strip()
        if v.startswith('"') and v.endswith('"'):
            v = json.loads(v)
        elif len(v) > 1 and v.startswith("'") and v.endswith("'"):
            v = v[1:-1].replace("''", "'")
        out[k.strip()] = v
    return out


def resolve(href):
    path, _, anchor = href.partition("#")
    path = path.rstrip("/")
    for _ in range(5):
        if path in redirects:
            path = redirects[path].split("#")[0]
    page = path.lstrip("/")
    f = f"{ROOT}/{page}.mdx"
    if not os.path.exists(f):
        return None
    fm = frontmatter(f)
    icon = fm.get("icon") or group_icon.get(page) or "file-lines"
    return icon, "" if anchor else fm.get("description", "")


missing = []
stale = []
for dirpath, _, files in os.walk(ROOT):
    rel = os.path.relpath(dirpath, ROOT)
    if "node_modules" in rel or (rel.startswith(".") and rel != "."):
        continue
    for name in files:
        if not name.endswith(".mdx"):
            continue
        f = os.path.join(dirpath, name)
        s = open(f).read()
        m = re.search(r"<Related links=\{\[\n(.*?)\n\]\} />", s, re.S)
        if not m:
            continue
        links = [json.loads(l.strip().rstrip(",")) for l in m.group(1).splitlines() if l.strip()]
        out = []
        for title, href, _, _ in links:
            r = resolve(href)
            if r is None:
                missing.append(f"{os.path.relpath(f, ROOT)}: {href}")
                r = ("file-lines", "")
            out.append([title, href, *r])
        body = ",\n  ".join(json.dumps(l, ensure_ascii=False) for l in out)
        s2 = s[:m.start()] + f"<Related links={{[\n  {body},\n]}} />" + s[m.end():]
        if s2 != s:
            stale.append(os.path.relpath(f, ROOT))
            if not DRY:
                open(f, "w").write(s2)

print(("out of date: " if DRY else "rewrote: ") + (", ".join(stale) or "none"))
for m in missing:
    print("link to a missing page:", m)
sys.exit(1 if (DRY and stale) or missing else 0)
