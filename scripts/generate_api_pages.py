#!/usr/bin/env python3
"""
Write the reference part of every API endpoint page from the OpenAPI spec.

Each page keeps its hand-written text. The script sets the title to the method and
path, then writes the parameter, body and response tables and the examples between
the GENERATED markers. Run it again after each API change.

The pages are SaturnDocs pages in site/pages/. The script also writes the sidebar
entries in site/docs.json, the API Playground operations in
site/components/operations.json and the endpoint title rules in site/public/theme.css.

Usage: python3 scripts/generate_api_pages.py [spec_path_or_url]
"""

import glob
import json
import os
import re
import sys
import urllib.request
import uuid

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_DIR = os.path.join(DOCS_DIR, "site")
PAGES_DIR = os.path.join(SITE_DIR, "pages")
NAV_FILE = os.path.join(SITE_DIR, "docs.json")
OPERATIONS_FILE = os.path.join(SITE_DIR, "components", "operations.json")
THEME_FILE = os.path.join(SITE_DIR, "public", "theme.css")
SPEC_URL = "https://api.getbluejay.ai/openapi.json"
BASE_URL = "https://api.getbluejay.ai"
PAGE_GLOBS = ["api-reference/endpoint/*.mdx", "api-reference/webhook/*.mdx"]
START = "{/* GENERATED: from the OpenAPI spec by scripts/generate_api_pages.py. Do not edit by hand. */}"
END = "{/* END GENERATED */}"
# The theme draws the method pill and the path of each endpoint title from one rule per page, between these markers.
TITLE_START = "/* GENERATED: endpoint titles, from the API pages by scripts/generate_api_pages.py. Do not edit by hand. */"
TITLE_END = "/* END GENERATED: endpoint titles */"
TITLE_METHODS = ("GET", "POST", "PUT", "PATCH", "DELETE")
MAX_DEPTH = 6
METHODS = ("get", "post", "put", "patch", "delete")
ENDPOINT_DIR = "api-reference/endpoint"
# Routes that get no page. A line is "METHOD /path". Delete a line to give that route a page.
IGNORE_FILE = "scripts/api-ignore.txt"
OTHER_GROUP = "Other"
PRIVATE_SEGMENTS = {"internal", "admin", "health", ".well-known", "ping"}
# ponytail: AccentType still lists old values the API accepts but that name a voice, not an accent.
# Drop this once the API's enum lists only real accents.
OLD_ACCENTS = re.compile(r"american2|mature|nigerian|watson\w*|fish\w*")
ACCENT_NOTE = "[GET /v1/voices](/api-reference/endpoint/list-voices) lists the accents of each language."


def is_private(path, op):
    """Routes for staff, health checks and the platform. These never get a page."""
    parts = path.strip("/").split("/")
    if PRIVATE_SEGMENTS & set(parts) or any("bbb" in x for x in parts):
        return True
    return any("internal" in x.get("name", "").lower() for x in op.get("parameters", []))


def load_spec(source):
    if source.startswith("http"):
        with urllib.request.urlopen(source, timeout=60) as r:
            return json.load(r)
    with open(source) as f:
        return json.load(f)


def resolve(spec, node, seen=()):
    """Return (schema, ref name) with $ref and allOf merged in."""
    name = None
    while isinstance(node, dict) and "$ref" in node:
        ref = node["$ref"]
        if ref in seen:
            return {"type": "object", "title": ref.rsplit("/", 1)[-1]}, ref.rsplit("/", 1)[-1]
        seen = seen + (ref,)
        name = ref.rsplit("/", 1)[-1]
        target = spec
        for part in ref.lstrip("#/").split("/"):
            target = target[part]
        node = {**target, **{k: v for k, v in node.items() if k != "$ref"}}
    if isinstance(node, dict) and "allOf" in node:
        merged = {k: v for k, v in node.items() if k != "allOf"}
        props, required = {}, []
        for part in node["allOf"]:
            sub, sub_name = resolve(spec, part, seen)
            name = name or sub_name
            props.update(sub.get("properties", {}))
            required += sub.get("required", [])
            for k, v in sub.items():
                if k not in ("properties", "required"):
                    merged.setdefault(k, v)
        if props:
            merged["properties"] = {**props, **merged.get("properties", {})}
        if required:
            merged["required"] = required + merged.get("required", [])
        node = merged
    return node, name


def non_null(spec, schema, seen=()):
    """Drop the null branch of anyOf/oneOf. Returns (variants, nullable)."""
    schema, _ = resolve(spec, schema, seen)
    for key in ("anyOf", "oneOf"):
        if key in schema:
            variants = [v for v in schema[key] if v.get("type") != "null"]
            nullable = len(variants) < len(schema[key])
            out = []
            for v in variants:
                rv, nm = resolve(spec, v, seen)
                if nm and "title" not in rv:
                    rv = {**rv, "title": nm}
                out.append(rv)
            extra = {k: v for k, v in schema.items() if k not in (key,)}
            if len(out) == 1:
                return [{**out[0], **{k: v for k, v in extra.items() if k in ("description", "default", "example")}}], nullable
            return out or [{}], nullable
    return [schema], False


def type_label(spec, schema, seen=()):
    variants, nullable = non_null(spec, schema, seen)
    labels = []
    for v in variants:
        t = v.get("type")
        if t == "array":
            inner = type_label(spec, v.get("items", {}), seen)
            labels.append(f"{inner}[]" if " " not in inner else f"array of {inner}")
        elif t in ("object", None) and ("properties" in v or v.get("title")) and t != "string":
            labels.append("object")
        elif v.get("format") == "binary" or "contentMediaType" in v:
            labels.append("file")
        elif v.get("format") in ("uuid", "date-time", "date", "uri", "email"):
            labels.append(f"{t} ({v['format']})")
        else:
            labels.append(t or "any")
    label = " or ".join(dict.fromkeys(labels))
    return label + (" or null" if nullable else "")


def object_children(spec, schema, depth, seen=()):
    """Rows for the properties of an object, or of the items of an array of objects."""
    if depth >= MAX_DEPTH:
        return []
    variants, _ = non_null(spec, schema, seen)
    rows = []
    for v in variants:
        target = v
        if v.get("type") == "array":
            target, _ = resolve(spec, v.get("items", {}), seen)
            inner, _ = non_null(spec, target, seen)
            target = inner[0] if len(inner) == 1 else target
        props = target.get("properties")
        if props:
            rows += field_rows(spec, props, target.get("required", []), depth + 1, seen)
        extra = target.get("additionalProperties")
        if isinstance(extra, dict) and extra:
            rows.append({"name": "{key}", "type": type_label(spec, extra, seen), "required": False,
                         "description": "Any key.", "children": object_children(spec, extra, depth + 1, seen)})
    return rows


def clean(text):
    if not text:
        return ""
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text.replace("—", ",")


def mdx_text(text):
    """Spec text as page text. Outside backticks, SaturnDocs reads { } and a tag-like < as code and rejects the page."""
    parts = re.split(r"(`+[^`]*`+)", text)
    return "".join(p if i % 2 else re.sub(r"([{}]|<(?=[A-Za-z_$/>!?]))", r"\\\1", p) for i, p in enumerate(parts))


def field_rows(spec, props, required, depth=0, seen=()):
    rows = []
    for name, raw in props.items():
        schema, _ = resolve(spec, raw, seen)
        variants, _ = non_null(spec, schema, seen)
        first = variants[0] if len(variants) == 1 else schema
        row = {
            "name": name,
            "type": type_label(spec, schema, seen),
            "required": name in required,
            "description": clean(schema.get("description") or first.get("description")),
        }
        default = schema.get("default", first.get("default"))
        if default is not None and not isinstance(default, (dict, list)):
            row["default"] = default
        enum = first.get("enum") or (first.get("items", {}) or {}).get("enum")
        if enum:
            row["values"] = [str(e) for e in enum]
        if first.get("title") == "AccentType":
            row["values"] = [v for v in row["values"] if not OLD_ACCENTS.fullmatch(v)]
            row["description"] = f"{row['description'].rstrip('.')}. {ACCENT_NOTE}".lstrip(". ")
        children = object_children(spec, schema, depth, seen)
        if children:
            row["children"] = children
        rows.append(row)
    return rows


def param_rows(spec, params, where):
    rows = []
    for p in params:
        if p.get("in") != where:
            continue
        schema, _ = resolve(spec, p.get("schema", {}))
        variants, _ = non_null(spec, schema)
        first = variants[0] if len(variants) == 1 else schema
        row = {
            "name": p["name"],
            "type": type_label(spec, schema),
            "required": bool(p.get("required")),
            "description": clean(p.get("description") or schema.get("description") or first.get("description")),
        }
        default = schema.get("default", first.get("default"))
        if default is not None and not isinstance(default, (dict, list)):
            row["default"] = default
        enum = first.get("enum") or (first.get("items", {}) or {}).get("enum")
        if enum:
            row["values"] = [str(e) for e in enum]
        rows.append(row)
    return rows


def example(spec, schema, depth=0, seen=(), name=""):
    schema, _ = resolve(spec, schema, seen)
    if "example" in schema:
        return schema["example"]
    if schema.get("examples") and isinstance(schema["examples"], list):
        return schema["examples"][0]
    variants, _ = non_null(spec, schema, seen)
    v = variants[0]
    if "example" in v:
        return v["example"]
    if v.get("enum"):
        return v["enum"][0]
    if "default" in schema and schema["default"] is not None:
        return schema["default"]
    t = v.get("type")
    if t == "array":
        return [example(spec, v.get("items", {}), depth + 1, seen)] if depth < MAX_DEPTH else []
    if t == "object" or "properties" in v:
        if depth >= MAX_DEPTH:
            return {}
        out = {k: example(spec, s, depth + 1, seen, k) for k, s in v.get("properties", {}).items()}
        extra = v.get("additionalProperties")
        if not out and isinstance(extra, dict) and extra:
            out = {"key": example(spec, extra, depth + 1, seen)}
        return out
    fmt = v.get("format")
    if t == "string":
        if fmt == "uuid":
            # One uuid per field name, so two ids in one example never look like the same object.
            return str(uuid.uuid5(uuid.NAMESPACE_URL, name)) if name else "3c90c3cc-0d44-4b50-8888-8dd25736052a"
        if fmt == "date-time":
            return "2026-01-01T00:00:00Z"
        if fmt == "date":
            return "2026-01-01"
        if fmt in ("uri", "url"):
            return "https://example.com"
        if fmt == "email":
            return "name@example.com"
        return "<string>"
    if t == "integer":
        return 123
    if t == "number":
        return 1.5
    if t == "boolean":
        return True
    return None


def body_schema(op):
    content = (op.get("requestBody") or {}).get("content", {})
    for ctype in ("application/json", "multipart/form-data", "application/x-www-form-urlencoded"):
        if ctype in content:
            return ctype, content[ctype].get("schema", {}), bool(op["requestBody"].get("required"))
    return None, None, False


def success(op):
    for code in sorted(op.get("responses", {})):
        if code.startswith("2"):
            return code, op["responses"][code]
    return None, None


def curl(spec, method, path, op):
    lines = [f"curl --request {method.upper()} \\", f"  --url {BASE_URL}{path} \\"]
    query = [p for p in op.get("parameters", []) if p.get("in") == "query" and p.get("required")]
    if query:
        qs = "&".join(f"{p['name']}=<{p['name']}>" for p in query)
        lines[1] = f"  --url '{BASE_URL}{path}?{qs}' \\"
    lines.append("  --header 'X-API-Key: <api-key>'")
    ctype, schema, _ = body_schema(op)
    if ctype == "application/json":
        lines[-1] += " \\"
        lines.append("  --header 'Content-Type: application/json' \\")
        body = json.dumps(example(spec, schema), indent=2)
        lines.append("  --data '" + body.replace("'", "'\\''").replace("\n", "\n  ") + "'")
    elif ctype == "multipart/form-data":
        resolved, _ = resolve(spec, schema)
        fields = list(resolved.get("properties", {}).items())
        for i, (name, s) in enumerate(fields):
            lines[-1] += " \\"
            is_file = type_label(spec, s).startswith("file")
            lines.append(f"  --form '{name}=@/path/to/file'" if is_file else f"  --form {name}=<{name}>")
    return "\n".join(lines)


def table(rows):
    return "<FieldTable rows={" + json.dumps(rows, ensure_ascii=False) + "} />"


def generate(spec, method, path, op):
    parts = [START, ""]
    params = op.get("parameters", [])
    for where, heading in (("path", "Path parameters"), ("query", "Query parameters"), ("header", "Headers")):
        rows = param_rows(spec, params, where)
        if where == "header":
            # An API key decides the workspace, so the API ignores X-Organization-Id for key callers.
            rows = [r for r in rows if r["name"] not in ("X-API-Key", "X-Organization-Id")]
            rows.insert(0, {"name": "X-API-Key", "type": "string", "required": True,
                            "description": "API key required to authenticate requests."})
        if rows:
            parts += [f"## {heading}", "", table(rows), ""]
    ctype, schema, body_required = body_schema(op)
    if schema is not None:
        resolved, _ = resolve(spec, schema)
        rows = field_rows(spec, resolved.get("properties", {}), resolved.get("required", []))
        variants, _ = non_null(spec, schema)
        note = "" if ctype == "application/json" else f"Send the body as `{ctype}`.\n\n"
        if not rows and len(variants) > 1 and all(v.get("properties") for v in variants):
            parts += ["## Request body", "", note + "Send one of these bodies.", ""]
            for v in variants:
                parts += [f"### {v.get('title')}", "", table(field_rows(spec, v["properties"], v.get("required", []))), ""]
        else:
            if not rows:
                rows = [{"name": "body", "type": type_label(spec, schema), "required": body_required,
                         "children": object_children(spec, schema, 0)}]
            parts += ["## Request body", "", note + table(rows), ""]
    code, resp = success(op)
    resp_schema = None
    if resp:
        resp_json = resp.get("content", {}).get("application/json")
        resp_schema = (resp_json or {}).get("schema")
        parts += [f"## Response", ""]
        if resp_schema:
            resolved, _ = resolve(spec, resp_schema)
            rows = field_rows(spec, resolved.get("properties", {}), resolved.get("required", []))
            if not rows and resolved.get("type") == "array":
                rows = object_children(spec, resp_schema, -1)
                parts += ["The response is a list. Each item has these fields:" if rows
                          else f"The response is a list of `{type_label(spec, resolved.get('items', {}))}`.", ""]
            elif not rows:
                rows = object_children(spec, resp_schema, -1)
                if not rows:
                    parts += [f"The response is `{type_label(spec, resp_schema)}`.", ""]
            if rows:
                parts += [table(rows), ""]
        elif resp_json is not None:
            parts += ["The response is JSON.", ""]
        else:
            parts += [f"A `{code}` response has no body.", ""]
    statuses = [(c, clean(r.get("description"))) for c, r in sorted(op.get("responses", {}).items())]
    if statuses:
        parts += ["## Status codes", "", "| Status | Meaning |", "|---|---|"]
        parts += [f"| `{c}` | {mdx_text(d)} |" for c, d in statuses]
        parts += [""]
    parts += ["## Example request", "", "```bash", curl(spec, method, path, op), "```", ""]
    if resp_schema:
        parts += ["## Example response", "", "```json " + code, json.dumps(example(spec, resp_schema), indent=2), "```", ""]
    parts.append(END)
    return "\n".join(parts)


def generate_webhook(spec, name, op):
    parts = [START, ""]
    _, schema, _ = body_schema(op)
    if schema is not None:
        resolved, _ = resolve(spec, schema)
        mapping = (resolved.get("discriminator") or {}).get("mapping", {})
        events = [(event, {"$ref": ref}) for event, ref in mapping.items()] or [("Payload", schema)]
        for event, event_schema in events:
            body, _ = resolve(spec, event_schema)
            rows = field_rows(spec, body.get("properties", {}), body.get("required", []))
            parts += [f"## `{event}`" if mapping else "## Payload", ""]
            if body.get("description"):
                parts += [mdx_text(clean(body["description"])), ""]
            parts += [table(rows), "", "```json Example", json.dumps(example(spec, event_schema), indent=2), "```", ""]
    parts.append(END)
    return "\n".join(parts)


FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
PROMPT_RE = [
    re.compile(r'<Accordion title="Prompt for AI agents".*?\n</Accordion>\n?', re.S),
    re.compile(r'<div className="ai-prompt-box">.*?````\n</div>\n?', re.S),
]


def set_key(fm, key, value):
    line = f'{key}: "{value}"'
    if re.search(rf"^{key}:", fm, re.M):
        return re.sub(rf"^{key}:.*$", line.replace("\\", "\\\\"), fm, flags=re.M)
    return fm + "\n" + line


def operation_of(fm):
    m = re.search(r'^api:\s*["\']?([A-Z]+) https?://[^/]+([^"\'\n]+)', fm, re.M)
    if m:
        return m.group(1), m.group(2).strip()
    return None


def titled_operation(fm):
    """The route of a page: its api key, or its "METHOD /path" title when the page has no api key."""
    found = operation_of(fm)
    if found:
        return found
    m = re.search(r'^title:\s*"?(%s) (/[^"\s]*)"?\s*$' % "|".join(TITLE_METHODS), fm, re.M)
    return (m.group(1), m.group(2)) if m else None


def ordered(fm):
    """Frontmatter with the title and description first and the generated keys last."""
    lines = fm.split("\n")
    if any(not re.match(r"[A-Za-z][\w:-]*:", ln) for ln in lines):
        return fm
    key = lambda ln: ln.split(":", 1)[0]
    first = [ln for k in ("title", "description") for ln in lines if key(ln) == k]
    last = [ln for k in ("api", "playground", "deprecated") for ln in lines if key(ln) == k]
    return "\n".join(first + [ln for ln in lines if ln not in first and ln not in last] + last)


def webhook_name(spec, page):
    """A webhook page is named after its webhook: events-webhook.mdx documents events_webhook."""
    stem = os.path.splitext(os.path.basename(page))[0]
    return next((n for n in (stem.replace("-", "_"), stem) if n in spec.get("webhooks", {})), None)


def page_file(slug):
    return os.path.join(PAGES_DIR, slug + ".mdx")


def leaf(entry):
    """The page of a sidebar entry, or None when the entry is a group."""
    return entry if isinstance(entry, str) else entry.get("page")


def process(spec, page):
    text = open(page).read()
    m = FM_RE.match(text)
    if not m:
        return "no frontmatter"
    fm, body = m.group(1), text[m.end():]
    for rx in PROMPT_RE:
        body = rx.sub("", body)
    body = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", body, flags=re.S)
    body = body.strip("\n")

    if os.path.basename(os.path.dirname(page)) == "webhook":
        name = webhook_name(spec, page)
        op = next(iter(spec["webhooks"][name].values()), None) if name else None
        if not op:
            return "webhook not in spec"
        generated = generate_webhook(spec, name, op)
    else:
        found = operation_of(fm)
        if not found:
            return "no api key"
        method, path = found
        op = spec["paths"].get(path, {}).get(method.lower())
        if not op:
            return f"{method} {path} not in spec"
        fm = set_key(fm, "title", f"{method} {path}")
        fm = set_key(fm, "api", f"{method} {BASE_URL}{path}")
        fm = set_key(fm, "playground", "none")
        fm = re.sub(r"^deprecated:.*\n?", "", fm, flags=re.M).rstrip("\n")
        if op.get("deprecated"):
            fm += "\ndeprecated: true"
        fm = ordered(fm)
        generated = generate(spec, method, path, op)

    out = f"---\n{fm}\n---\n\n"
    if body:
        out += body + "\n\n"
    out += generated + "\n"
    if out != text:
        open(page, "w").write(out)
    return None


def nav_endpoints():
    """(group label, slug) for every endpoint page, in API sidebar order. Hidden groups are left out."""
    tabs = json.load(open(NAV_FILE))["navigation"]["tabs"]
    api = next(t for t in tabs if t["tab"] == "API")

    def walk(group, label):
        for p in group["pages"]:
            slug = leaf(p)
            if slug is None:
                if not p.get("hidden"):
                    yield from walk(p, p["group"])
            elif "/endpoint/" in slug:
                yield label, slug

    for top in api["groups"]:
        if not top.get("hidden"):
            yield from walk(top, top["group"])


def write_operations(spec):
    ops = []
    for group, slug in nav_endpoints():
        fm = FM_RE.match(open(page_file(slug)).read())
        found = titled_operation(fm.group(1)) if fm else None
        if not found:
            continue
        method, path = found
        op = spec["paths"].get(path, {}).get(method.lower())
        if not op:
            continue
        params = [{"name": p["name"], "in": p["in"], "required": bool(p.get("required"))}
                  for p in op.get("parameters", []) if p["in"] in ("path", "query")]
        ctype, schema, _ = body_schema(op)
        body = json.dumps(example(spec, schema), indent=2) if ctype == "application/json" else None
        ops.append({"group": group, "slug": slug, "method": method, "path": path,
                    "summary": op.get("summary", ""), "params": params, "body": body,
                    "bodyType": ctype})
    content = json.dumps(ops, indent=2, ensure_ascii=False) + "\n"
    if not os.path.exists(OPERATIONS_FILE) or open(OPERATIONS_FILE).read() != content:
        open(OPERATIONS_FILE, "w").write(content)
    return len(ops)


def path_parts(path):
    """Path segments without the version, so /v2/x lands next to /v1/x."""
    parts = path.strip("/").split("/")
    return parts[1:] if parts and re.fullmatch(r"v\d+", parts[0]) else parts


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def nav_groups(tab):
    """(group, index, method, path) for every endpoint page in the tab. Hidden groups are left out."""
    def walk(group):
        for i, p in enumerate(group["pages"]):
            slug = leaf(p)
            if slug is None:
                if not p.get("hidden"):
                    yield from walk(p)
            elif "/endpoint/" in slug:
                fm = FM_RE.match(open(page_file(slug)).read())
                found = titled_operation(fm.group(1)) if fm else None
                if found:
                    yield group, i, found[0], found[1]

    for top in tab["groups"]:
        if not top.get("hidden"):
            yield from walk(top)


def sidebar_entry(slug, method, path):
    """A sidebar entry with the method pill. A zero-width space after each slash lets a long path wrap at a slash."""
    return {"page": slug, "label": path.replace("/", "/\u200b"), "method": method}


def stub_page(spec, method, path, op):
    summary = clean(op.get("summary")) or f"{method} {path}"
    intro = clean((op.get("description") or "").split("\n\n")[0]) or summary + "."
    description = json.dumps(summary.replace(chr(34), chr(39)), ensure_ascii=False)
    page = f'---\ndescription: {description}\napi: "{method} {BASE_URL}{path}"\n---\n\n{mdx_text(intro)}\n'
    slug = slugify(summary)
    version = path.strip("/").split("/")[0]
    candidates = [slug, f"{slug}-{version}", f"{slug}-{version}-{method.lower()}"]
    candidates += [f"{candidates[-1]}-{n}" for n in range(2, 100)]
    slug = next(c for c in candidates if not os.path.exists(page_file(f"{ENDPOINT_DIR}/{c}")))
    open(page_file(f"{ENDPOINT_DIR}/{slug}"), "w").write(page)
    return f"{ENDPOINT_DIR}/{slug}"


def add_new_pages(spec):
    """Stub a page and a nav entry for each spec route with no page that is not in IGNORE_FILE."""
    ignore_path = os.path.join(DOCS_DIR, IGNORE_FILE)
    ignored = {ln.strip() for ln in open(ignore_path) if ln.strip() and not ln.startswith("#")}
    docs = json.load(open(NAV_FILE))
    tab = next(t for t in docs["navigation"]["tabs"] if t["tab"] == "API")
    have = set()
    for page in glob.glob(os.path.join(PAGES_DIR, ENDPOINT_DIR, "*.mdx")):
        fm = FM_RE.match(open(page).read())
        found = titled_operation(fm.group(1)) if fm else None
        if found:
            have.add(found)
    new = sorted((p, m.upper()) for p, item in spec["paths"].items() for m in item
                 if m in METHODS and (m.upper(), p) not in have and f"{m.upper()} {p}" not in ignored
                 and not is_private(p, item[m]))
    added = []
    for path, method in new:
        slug = stub_page(spec, method, path, spec["paths"][path][method.lower()])
        best, score = None, 0
        for group, i, m, p in nav_groups(tab):
            a, b = path_parts(path), path_parts(p)
            common = next((k for k, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            if common > score or (common == score and best and group is best[0]):
                best, score = (group, i), common
        if best:
            best[0]["pages"].insert(best[1] + 1, sidebar_entry(slug, method, path))
        else:
            other = next((g for g in tab["groups"] if g["group"] == OTHER_GROUP), None)
            if not other:
                other = {"group": OTHER_GROUP, "pages": []}
                # Hidden groups stay last.
                tab["groups"].insert(next((i for i, g in enumerate(tab["groups"]) if g.get("hidden")), len(tab["groups"])), other)
            other["pages"].append(sidebar_entry(slug, method, path))
        added.append(f"{method} {path} -> {slug}")
    if added:
        open(NAV_FILE, "w").write(json.dumps(docs, indent=2, ensure_ascii=False) + "\n")
    return added


def write_sidebar_entries():
    """Give every listed endpoint page its method pill and path label. Hidden groups keep plain entries."""
    docs = json.load(open(NAV_FILE))
    changed = 0

    def walk(group):
        nonlocal changed
        for i, p in enumerate(group["pages"]):
            slug = leaf(p)
            if slug is None:
                if not p.get("hidden"):
                    walk(p)
                continue
            if not slug.startswith(ENDPOINT_DIR + "/") or not os.path.exists(page_file(slug)):
                continue
            fm = FM_RE.match(open(page_file(slug)).read())
            found = operation_of(fm.group(1)) if fm else None
            if not found:
                continue
            old = p if isinstance(p, dict) else {}
            entry = {**sidebar_entry(slug, *found), **{k: v for k, v in old.items() if k not in ("page", "label", "method")}}
            entry = {**{k: entry[k] for k in ("page", "label", "icon", "method") if k in entry}, **entry}
            if entry != p or list(entry) != list(old):
                group["pages"][i] = entry
                changed += 1

    for tab in docs["navigation"]["tabs"]:
        for top in tab["groups"]:
            if not top.get("hidden"):
                walk(top)
    if changed:
        open(NAV_FILE, "w").write(json.dumps(docs, indent=2, ensure_ascii=False) + "\n")
    return changed


def titled_pages():
    """(route, method, path) for every page with a "METHOD /path" title: listed pages in sidebar order, then hidden ones."""
    listed, hidden = [], []

    def walk(group, out):
        out = hidden if group.get("hidden") else out
        if group.get("root"):
            out.append(group["root"])
        for p in group["pages"]:
            slug = leaf(p)
            if slug is None:
                walk(p, out)
            else:
                out.append(slug)

    for tab in json.load(open(NAV_FILE))["navigation"]["tabs"]:
        for top in tab["groups"]:
            walk(top, listed)
    pages = []
    for slug in dict.fromkeys(listed + hidden):
        if not os.path.exists(page_file(slug)):
            continue
        fm = FM_RE.match(open(page_file(slug)).read())
        m = re.search(r'^title:\s*"?(%s)\s+(/[^"\s]*)"?\s*$' % "|".join(TITLE_METHODS), fm.group(1), re.M) if fm else None
        if m:
            pages.append(("/" + slug, m.group(1), m.group(2)))
    return pages


def write_title_rules():
    """Write the theme rules that draw each endpoint title as a method pill and a path."""
    css = open(THEME_FILE).read()
    if css.count(TITLE_START) != 1 or css.count(TITLE_END) != 1:
        sys.exit(f"{os.path.relpath(THEME_FILE, DOCS_DIR)} needs one pair of endpoint title markers")
    start, end = css.index(TITLE_START), css.index(TITLE_END)
    pages = titled_pages()
    bad = [p for _, _, p in pages if not re.fullmatch(r"[\x21-\x7e]+", p) or '"' in p or "\\" in p]
    if bad:
        sys.exit(f"These paths cannot be written to the theme: {bad}")
    known = re.search(r'\{\n(  --bj-title-method: "(\w+)";\n(?:  .*\n)*?)\}', css[start:end])
    body, model = (known.group(1), known.group(2)) if known else ('  --bj-title-method: "GET";\n  --bj-method-bg: var(--bj-method-get-bg);\n  --bj-method-fg: var(--bj-method-get-fg);\n', "GET")
    lines = [TITLE_START]
    for method in TITLE_METHODS:
        links = ", ".join(f'[href$="{route}"]' for route, m, _ in pages if m == method)
        if links:
            rule = body.replace(f'"{model}"', f'"{method}"').replace(f"-{model.lower()}-", f"-{method.lower()}-")
            lines.append(f'html:has(link[rel="canonical"]:is({links})) {{\n{rule}}}')
    lines += [f'html:has(link[rel="canonical"][href$="{route}"]) {{ --bj-title-path: "{path}"; }}' for route, _, path in pages]
    out = css[:start] + "\n".join(lines) + "\n" + css[end:]
    if out != css:
        open(THEME_FILE, "w").write(out)
    return len(pages)


def main():
    spec = load_spec(sys.argv[1] if len(sys.argv) > 1 else SPEC_URL)
    added = add_new_pages(spec)
    print(f"new pages: {len(added)}")
    for a in added:
        print("  " + a)
    problems = []
    pages = sorted(p for g in PAGE_GLOBS for p in glob.glob(os.path.join(PAGES_DIR, g)))
    for page in pages:
        err = process(spec, page)
        if err:
            problems.append(f"{os.path.relpath(page, DOCS_DIR)}: {err}")
    print(f"pages: {len(pages)}, skipped: {len(problems)}")
    for p in problems:
        print("  " + p)
    print(f"API Playground operations: {write_operations(spec)}")
    print(f"sidebar entries updated: {write_sidebar_entries()}")
    print(f"endpoint title rules: {write_title_rules()}")


if __name__ == "__main__":
    main()
