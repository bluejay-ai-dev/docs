#!/usr/bin/env python3
"""
Write the reference part of every API endpoint page from the OpenAPI spec.

Each page keeps its hand-written text. The script sets the title to the method and
path, then writes the parameter, body and response tables and the examples between
the GENERATED markers. Run it again after each API change.

Usage: python3 scripts/generate_api_pages.py [spec_path_or_url]
"""

import glob
import json
import os
import re
import sys
import urllib.request

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC_URL = "https://api.getbluejay.ai/openapi.json"
BASE_URL = "https://api.getbluejay.ai"
PAGE_GLOBS = ["api-reference/endpoint/*.mdx", "api-reference/webhook/*.mdx"]
IMPORT = 'import { FieldTable } from "/snippets/field-table.jsx";'
START = "{/* GENERATED: from the OpenAPI spec by scripts/generate_api_pages.py. Do not edit by hand. */}"
END = "{/* END GENERATED */}"
MAX_DEPTH = 6
METHODS = ("get", "post", "put", "patch", "delete")


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
        elif v.get("format") in ("uuid", "date-time", "date", "uri", "email", "binary"):
            labels.append(f"{t} ({v['format']})" if v["format"] != "binary" else "file")
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
    if depth >= MAX_DEPTH:
        return {} if t == "object" else None
    if t == "array":
        return [example(spec, v.get("items", {}), depth + 1, seen)]
    if t == "object" or "properties" in v:
        out = {k: example(spec, s, depth + 1, seen, k) for k, s in v.get("properties", {}).items()}
        extra = v.get("additionalProperties")
        if not out and isinstance(extra, dict) and extra:
            out = {"key": example(spec, extra, depth + 1, seen)}
        return out
    fmt = v.get("format")
    if t == "string":
        if fmt == "uuid":
            return "3c90c3cc-0d44-4b50-8888-8dd25736052a"
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
            is_file = type_label(spec, s) == "file"
            lines.append(f"  --form {name}=@<file>" if is_file else f"  --form {name}=<{name}>")
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
        if not rows:
            rows = [{"name": "body", "type": type_label(spec, schema), "required": body_required,
                     "children": object_children(spec, schema, 0)}]
        note = "" if ctype == "application/json" else f"Send the body as `{ctype}`.\n\n"
        parts += ["## Request body", "", note + table(rows), ""]
    code, resp = success(op)
    resp_schema = None
    if resp:
        resp_schema = (resp.get("content", {}).get("application/json") or {}).get("schema")
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
        else:
            parts += [f"A `{code}` response has no body.", ""]
    statuses = [(c, clean(r.get("description"))) for c, r in sorted(op.get("responses", {}).items())]
    if statuses:
        parts += ["## Status codes", "", "| Status | Meaning |", "|---|---|"]
        parts += [f"| `{c}` | {d} |" for c, d in statuses]
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
                parts += [clean(body["description"]), ""]
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
    m = re.search(r'^openapi:\s*["\']?([A-Z]+) ([^"\'\n]+)', fm, re.M)
    if m:
        return m.group(1), m.group(2).strip()
    m = re.search(r'^api:\s*["\']?([A-Z]+) https?://[^/]+([^"\'\n]+)', fm, re.M)
    if m:
        return m.group(1), m.group(2).strip()
    return None


def process(spec, page):
    text = open(page).read()
    m = FM_RE.match(text)
    if not m:
        return "no frontmatter"
    fm, body = m.group(1), text[m.end():]
    for rx in PROMPT_RE:
        body = rx.sub("", body)
    body = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", body, flags=re.S)
    body = body.replace(IMPORT + "\n", "").strip("\n")

    webhook = re.search(r'^(?:openapi:\s*["\']?WEBHOOK |webhook:\s*["\']?)(\w+)["\']?$', fm, re.M)
    if webhook:
        op = next(iter(spec.get("webhooks", {}).get(webhook.group(1), {}).values()), None)
        if not op:
            return "webhook not in spec"
        fm = re.sub(r"^openapi:.*\n?", "", fm, flags=re.M).rstrip("\n")
        fm = set_key(fm, "webhook", webhook.group(1))
        generated = generate_webhook(spec, webhook.group(1), op)
    else:
        found = operation_of(fm)
        if not found:
            return "no operation"
        method, path = found
        op = spec["paths"].get(path, {}).get(method.lower())
        if not op:
            return f"{method} {path} not in spec"
        fm = re.sub(r"^openapi:.*\n?", "", fm, flags=re.M).rstrip("\n")
        fm = set_key(fm, "title", f"{method} {path}")
        # A zero-width space after each slash lets a long path wrap at a slash, not inside a word.
        fm = set_key(fm, "sidebarTitle", path.replace("/", "/\\u200b"))
        fm = set_key(fm, "api", f"{method} {BASE_URL}{path}")
        fm = set_key(fm, "playground", "none")
        generated = generate(spec, method, path, op)

    out = f"---\n{fm}\n---\n\n{IMPORT}\n\n"
    if body:
        out += body + "\n\n"
    out += generated + "\n"
    if out != text:
        open(page, "w").write(out)
    return None


def nav_endpoints():
    """(group label, slug) for every endpoint page, in API sidebar order."""
    tabs = json.load(open(os.path.join(DOCS_DIR, "docs.json")))["navigation"]["tabs"]
    api = next(t for t in tabs if t["tab"] == "API")

    def walk(group, label):
        for p in group["pages"]:
            if isinstance(p, dict):
                yield from walk(p, p["group"])
            elif "/endpoint/" in p:
                yield label, p

    for top in api["groups"]:
        yield from walk(top, top["group"])


def write_operations(spec):
    ops = []
    for group, slug in nav_endpoints():
        fm = FM_RE.match(open(os.path.join(DOCS_DIR, slug + ".mdx")).read())
        found = operation_of(fm.group(1)) if fm else None
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
    out = os.path.join(DOCS_DIR, "snippets", "api-operations.jsx")
    content = ("// Generated by scripts/generate_api_pages.py from the OpenAPI spec. Do not edit by hand.\n"
               "export const apiOperations = " + json.dumps(ops, ensure_ascii=False) + ";\n")
    if not os.path.exists(out) or open(out).read() != content:
        open(out, "w").write(content)
    return len(ops)


def main():
    spec = load_spec(sys.argv[1] if len(sys.argv) > 1 else SPEC_URL)
    problems = []
    pages = sorted(p for g in PAGE_GLOBS for p in glob.glob(os.path.join(DOCS_DIR, g)))
    for page in pages:
        err = process(spec, page)
        if err:
            problems.append(f"{os.path.relpath(page, DOCS_DIR)}: {err}")
    print(f"pages: {len(pages)}, skipped: {len(problems)}")
    for p in problems:
        print("  " + p)
    print(f"API Playground operations: {write_operations(spec)}")


if __name__ == "__main__":
    main()
