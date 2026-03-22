#!/usr/bin/env python3
"""
Generate 'Copy AI Integration Prompt' Accordion dropdowns for every API endpoint MDX file.

Reads openapi.json, resolves $ref schemas, generates filled prompt templates,
and inserts <Accordion> blocks into each endpoint/webhook MDX file.
"""

import copy
import glob
import json
import os
import re
import sys

DOCS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPENAPI_PATH = os.path.join(DOCS_DIR, "api-reference", "openapi.json")
ENDPOINT_DIR = os.path.join(DOCS_DIR, "api-reference", "endpoint")
WEBHOOK_DIR = os.path.join(DOCS_DIR, "api-reference", "webhook")

BASE_URL = "https://api.getbluejay.ai"

SKIP_FILES = {"create.mdx", "get.mdx", "delete.mdx", "queue-simulation.mdx"}


def load_spec():
    with open(OPENAPI_PATH, "r") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Schema resolution
# ---------------------------------------------------------------------------

def resolve_ref(spec, ref, seen=None):
    """Dereference a $ref pointer, guarding against cycles."""
    if seen is None:
        seen = set()
    if ref in seen:
        return {}
    seen.add(ref)

    parts = ref.lstrip("#/").split("/")
    node = spec
    for part in parts:
        node = node.get(part, {})
    node = copy.deepcopy(node)
    return resolve_schema(spec, node, seen)


def resolve_schema(spec, schema, seen=None):
    """Recursively resolve all $ref pointers inside a schema."""
    if seen is None:
        seen = set()
    if not isinstance(schema, dict):
        return schema

    if "$ref" in schema:
        return resolve_ref(spec, schema["$ref"], seen.copy())

    result = {}
    for key, value in schema.items():
        if key == "properties" and isinstance(value, dict):
            result[key] = {
                pn: resolve_schema(spec, ps, seen.copy())
                for pn, ps in value.items()
            }
        elif key == "items" and isinstance(value, dict):
            result[key] = resolve_schema(spec, value, seen.copy())
        elif key in ("anyOf", "oneOf", "allOf") and isinstance(value, list):
            result[key] = [resolve_schema(spec, v, seen.copy()) for v in value]
        elif key == "$defs" and isinstance(value, dict):
            result[key] = {
                dn: resolve_schema(spec, ds, seen.copy())
                for dn, ds in value.items()
            }
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# Example generation
# ---------------------------------------------------------------------------

def schema_to_example(schema, depth=0):
    """Generate a minimal example value from a resolved JSON schema."""
    if depth > 5 or not schema or not isinstance(schema, dict):
        return None

    if "anyOf" in schema:
        for variant in schema["anyOf"]:
            if variant.get("type") != "null":
                return schema_to_example(variant, depth)
        return None

    if "oneOf" in schema:
        return schema_to_example(schema["oneOf"][0], depth) if schema["oneOf"] else None

    if "allOf" in schema:
        merged = {}
        for s in schema["allOf"]:
            merged.setdefault("properties", {}).update(s.get("properties", {}))
            merged.setdefault("required", []).extend(s.get("required", []))
            if "type" in s:
                merged["type"] = s["type"]
        return schema_to_example(merged, depth)

    if "enum" in schema:
        return schema["enum"][0]

    if "default" in schema and schema["default"] is not None:
        return schema["default"]

    t = schema.get("type")
    desc = (schema.get("description") or "").lower()
    title = (schema.get("title") or "").lower()

    if t == "string":
        if "url" in title or "url" in desc or "uri" in title or "uri" in desc:
            return "https://example.com"
        if "email" in title or "email" in desc:
            return "user@example.com"
        if "phone" in title or "phone" in desc:
            return "+15551234567"
        if "date" in title or "date" in desc:
            return "2024-01-01T00:00:00Z"
        if "prompt" in title:
            return "You are a helpful assistant."
        if "name" in title:
            return "example_name"
        return "string"

    if t == "integer":
        return 123
    if t == "number":
        return 1.0
    if t == "boolean":
        return True

    if t == "array":
        items = schema.get("items", {})
        item_ex = schema_to_example(items, depth + 1)
        return [item_ex] if item_ex is not None else []

    if t == "object" or "properties" in schema:
        props = schema.get("properties", {})
        obj = {}
        for pn, ps in props.items():
            val = schema_to_example(ps, depth + 1)
            if val is not None:
                obj[pn] = val
        if not props and schema.get("additionalProperties"):
            return {"key": "value"}
        return obj

    return "string"


# ---------------------------------------------------------------------------
# Type strings
# ---------------------------------------------------------------------------

def get_type_str(schema):
    """Human-readable type label from a schema."""
    if not schema or not isinstance(schema, dict):
        return "any"

    if "$ref" in schema:
        return schema["$ref"].split("/")[-1]

    if "anyOf" in schema:
        types = []
        nullable = False
        for v in schema["anyOf"]:
            if v.get("type") == "null":
                nullable = True
                continue
            if "$ref" in v:
                types.append(v["$ref"].split("/")[-1])
            else:
                types.append(get_type_str(v))
        s = " | ".join(types) if types else "any"
        if nullable:
            s += " (nullable)"
        return s

    if "oneOf" in schema:
        return " | ".join(get_type_str(v) for v in schema["oneOf"])

    t = schema.get("type", "any")

    if "enum" in schema:
        vals = ", ".join(str(e) for e in schema["enum"])
        return f"{t} (enum: {vals})"

    if t == "array":
        item_type = get_type_str(schema.get("items", {}))
        return f"array[{item_type}]"

    return t


# ---------------------------------------------------------------------------
# Parameter / body / response extraction
# ---------------------------------------------------------------------------

def extract_params(spec, operation):
    params = []
    for p in operation.get("parameters", []):
        resolved = resolve_schema(spec, p)
        ps = resolved.get("schema", {})
        params.append({
            "name": resolved.get("name", ""),
            "location": resolved.get("in", ""),
            "type": get_type_str(ps),
            "required": "yes" if resolved.get("required", False) else "no",
            "description": resolved.get("description", ps.get("description", "")),
        })
    return params


def extract_body_schema(spec, operation):
    rb = operation.get("requestBody", {})
    if not rb:
        return None
    schema = rb.get("content", {}).get("application/json", {}).get("schema", {})
    return resolve_schema(spec, schema) if schema else None


def extract_response(spec, operation):
    """Return (status_code, resolved_schema_or_None, description)."""
    responses = operation.get("responses", {})
    for code in ("200", "201", "202", "204"):
        if code in responses:
            resp = responses[code]
            desc = resp.get("description", "")
            schema = resp.get("content", {}).get("application/json", {}).get("schema", {})
            if schema:
                return code, resolve_schema(spec, schema), desc
            return code, None, desc
    return "200", None, "Successful Response"


def extract_error_codes(operation):
    errors = []
    for code, resp in operation.get("responses", {}).items():
        if code.startswith("4") or code.startswith("5"):
            errors.append(f"{code}: {resp.get('description', 'Error')}")
    return errors


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def sanitize_func_name(title):
    name = title.lower().replace(" ", "_").replace("-", "_")
    name = re.sub(r"[^a-z0-9_]", "", name)
    return name


def build_required_params_table(header_params, body_schema):
    """Build a parameter table containing only required params."""
    rows = []
    if header_params:
        for p in header_params:
            if p["required"] != "yes":
                continue
            desc = p["description"].replace("\n", " ").replace("|", "\\|")
            rows.append(f"| {p['name']} | {p['type']} | {desc} |")

    if body_schema and "properties" in body_schema:
        required = set(body_schema.get("required", []))
        for pn, ps in body_schema["properties"].items():
            if pn not in required:
                continue
            ts = get_type_str(ps)
            desc = (ps.get("description") or "").replace("\n", " ").replace("|", "\\|")
            rows.append(f"| {pn} | {ts} | {desc} |")

    if not rows:
        return "No required parameters."

    header = (
        "| Name | Type | Description |\n"
        "|------|------|-------------|"
    )
    return header + "\n" + "\n".join(rows)


def get_optional_param_names(header_params, body_schema, limit=6):
    """Collect a few optional parameter names for the docs directive."""
    names = []
    if header_params:
        for p in header_params:
            if p["required"] != "yes":
                names.append(p["name"])
    if body_schema and "properties" in body_schema:
        required = set(body_schema.get("required", []))
        for pn in body_schema["properties"]:
            if pn not in required:
                names.append(pn)
    return names[:limit]


def schema_to_required_example(body_schema):
    """Generate an example containing only required fields."""
    if not body_schema or "properties" not in body_schema:
        return None
    required = set(body_schema.get("required", []))
    if not required:
        return None
    obj = {}
    for pn, ps in body_schema["properties"].items():
        if pn not in required:
            continue
        val = schema_to_example(ps)
        if val is not None:
            obj[pn] = val
    return obj if obj else None


# ---------------------------------------------------------------------------
# Few-shot examples (Python / requests)
# ---------------------------------------------------------------------------

def _build_few_shot(method, path, title, has_body, param_types=None):
    fn = sanitize_func_name(title)
    path_params = re.findall(r"\{(\w+)\}", path)
    url_line_is_fstring = bool(path_params)
    param_types = param_types or {}

    sig_parts = [f"{p}: {param_types.get(p, 'str')}" for p in path_params]
    if has_body:
        sig_parts.append("payload: dict")
    sig_parts.append("api_key: str")
    sig = ", ".join(sig_parts)

    if url_line_is_fstring:
        url_line = f'    url = f"{BASE_URL}{path}"'
    else:
        url_line = f'    url = "{BASE_URL}{path}"'

    headers_line = '    headers = {"X-API-Key": api_key}'

    method_lower = method.lower()
    if has_body:
        call_line = f"    response = requests.{method_lower}(url, headers=headers, json=payload)"
    else:
        call_line = f"    response = requests.{method_lower}(url, headers=headers)"

    lines = [
        "```python",
        "import requests",
        "",
        f"def {fn}({sig}) -> dict:",
        url_line,
        headers_line,
        call_line,
        "    response.raise_for_status()",
        "    return response.json()",
        "```",
    ]
    return "\n".join(lines)


def generate_few_shot(method, path, title, has_body, param_types=None):
    method_upper = method.upper()
    label_map = {
        "GET": "Simple GET",
        "POST": "POST with body",
        "PUT": "PUT with body",
        "PATCH": "PATCH with body",
        "DELETE": "DELETE request",
    }
    label = label_map.get(method_upper, f"{method_upper} request")
    code = _build_few_shot(method, path, title, has_body, param_types)
    return f"**{label}:**\n{code}"


# ---------------------------------------------------------------------------
# Prompt generators
# ---------------------------------------------------------------------------

def generate_endpoint_prompt(spec, title, method, path, operation, docs_slug=""):
    method = method.upper()

    description = (operation.get("description") or "").strip()
    params = extract_params(spec, operation)
    body_schema = extract_body_schema(spec, operation)
    error_codes = extract_error_codes(operation)

    params_table = build_required_params_table(params, body_schema)
    optional_names = get_optional_param_names(params, body_schema)

    docs_url = f"https://docs.getbluejay.ai/api-reference/endpoint/{docs_slug}" if docs_slug else ""

    optional_directive = ""
    if optional_names:
        examples = ", ".join(f"`{n}`" for n in optional_names)
        ref = f" at {docs_url}" if docs_url else ""
        optional_directive = (
            f"\n\nReview the full parameter list{ref} and include any "
            f"optional parameters (e.g., {examples}) that serve your integration's "
            f"use case and align with Bluejay's testing and monitoring capabilities."
        )

    body_section = ""
    if body_schema:
        example = schema_to_required_example(body_schema)
        if example:
            body_json = json.dumps(example, indent=2)
            ref = f" at {docs_url}" if docs_url else " in the API documentation"
            body_section = (
                f"\n\n### Request Body (required fields)\n```json\n{body_json}\n```\n\n"
                f"Refer to the full schema{ref}. Include optional fields that serve "
                f"the goal of setting up for testing and monitoring on Bluejay."
            )
        else:
            full_example = schema_to_example(body_schema)
            if full_example:
                body_json = json.dumps(full_example, indent=2)
                body_section = f"\n\n### Request Body\n```json\n{body_json}\n```"

    ct_line = "\n**Content-Type:** application/json" if body_schema else ""

    openapi_type_map = {"integer": "int", "number": "float", "boolean": "bool"}
    param_types = {}
    for p in params:
        if p["location"] == "path":
            raw = p["type"].split()[0].strip("()")
            param_types[p["name"]] = openapi_type_map.get(raw, "str")

    few_shot = generate_few_shot(method, path, title, body_schema is not None, param_types)

    error_line = ""
    if error_codes:
        error_line = "; ".join(error_codes[:3])

    desc_clean = " ".join(description.split()) if description else ""
    desc_line = f"\n\n> **What this endpoint does:** {desc_clean}" if desc_clean else ""

    prompt = (
        f"# Bluejay \u2014 Testing & Monitoring Platform for Conversational AI Agents\n\n"
        f"You are a senior backend engineer integrating the Bluejay API. "
        f"Think step-by-step: first understand the endpoint, then plan the "
        f"integration, then implement with minimal changes.\n\n"
        f"## {title} \u2014 {method} {path}"
        f"{desc_line}\n\n"
        f"**Endpoint:** {method} `{BASE_URL}{path}`\n"
        f"**Auth:** `X-API-Key` header{ct_line}\n\n"
        f"### Required Parameters\n"
        f"{params_table}"
        f"{optional_directive}"
        f"{body_section}\n\n"
        f"### Example\n{few_shot}\n\n"
        f"### Constraints\n"
        f"- Minimal changes \u2014 only add/change files needed for this integration.\n"
        f"- Match existing codebase patterns (naming, file structure, error handling).\n"
    )
    if error_line:
        prompt += f"- Include error handling for {error_line}.\n"
    prompt += (
        f"\n### Integration Checklist\n"
        f"Before writing code, verify:\n"
        f"1. Which module/service owns this API domain in the codebase?\n"
        f"2. What HTTP client and error-handling patterns does the project use?\n"
        f"3. Are there existing types/interfaces to extend?\n\n"
        f"Then implement the integration, export it, and confirm it compiles/passes lint."
    )
    return prompt


def generate_webhook_prompt(spec, title, webhook_id, operation):
    description = operation.get("description", "")

    rb = operation.get("requestBody", {})
    raw_schema = rb.get("content", {}).get("application/json", {}).get("schema", {})
    resolved = resolve_schema(spec, raw_schema) if raw_schema else None

    payload_table_lines = []
    payload_examples = ""

    if resolved and "oneOf" in resolved:
        discriminator = resolved.get("discriminator", {})
        disc_prop = discriminator.get("propertyName", "type")
        mapping = discriminator.get("mapping", {})

        payload_examples = (
            f"\n\n### Payload Schema\n"
            f"Discriminated by `{disc_prop}`:\n"
        )
        payload_table_lines.append("| Name | Type | Required | Description |")
        payload_table_lines.append("|------|------|----------|-------------|")

        for vtype, vref in mapping.items():
            vs = resolve_ref(spec, vref)
            payload_table_lines.append(f"| **Variant: `{vtype}`** | | | |")
            req_fields = set(vs.get("required", []))
            for pn, ps in vs.get("properties", {}).items():
                if pn not in req_fields:
                    continue
                ts = get_type_str(ps)
                d = (ps.get("description") or "").replace("\n", " ").replace("|", "\\|")
                payload_table_lines.append(f"| {pn} | {ts} | yes | {d} |")

            example = schema_to_example(vs)
            if example:
                ej = json.dumps(example, indent=2)
                payload_examples += (
                    f"\n**When `{disc_prop}` = `{vtype}`:**\n```json\n{ej}\n```\n"
                )

    elif resolved and "properties" in resolved:
        payload_table_lines.append("| Name | Type | Required | Description |")
        payload_table_lines.append("|------|------|----------|-------------|")
        req_fields = set(resolved.get("required", []))
        for pn, ps in resolved["properties"].items():
            if pn not in req_fields:
                continue
            ts = get_type_str(ps)
            d = (ps.get("description") or "").replace("\n", " ").replace("|", "\\|")
            payload_table_lines.append(f"| {pn} | {ts} | yes | {d} |")
        example = schema_to_example(resolved)
        if example:
            ej = json.dumps(example, indent=2)
            payload_examples = f"\n\n### Payload Schema\n```json\n{ej}\n```"

    payload_table = "\n".join(payload_table_lines) if payload_table_lines else "See payload examples below."

    fn = sanitize_func_name(title)

    desc_clean = " ".join(description.split()) if description else ""
    desc_line = f"\n\n> **What this webhook does:** {desc_clean}" if desc_clean else ""

    prompt = (
        f"# Bluejay \u2014 Testing & Monitoring Platform for Conversational AI Agents\n\n"
        f"You are a senior backend engineer integrating the Bluejay API. "
        f"Think step-by-step: first understand the webhook payload, then plan "
        f"the handler, then implement with minimal changes.\n\n"
        f"## Handle {title} \u2014 WEBHOOK"
        f"{desc_line}\n\n"
        f"**Type:** Incoming Webhook (JSON POST)\n"
        f"\n### Required Payload Fields\n"
        f"{payload_table}"
        f"{payload_examples}\n\n"
        f"Refer to the Bluejay API documentation for additional optional payload fields.\n\n"
        f"### Example\n"
        f"```python\n"
        f"from fastapi import FastAPI, Request\n\n"
        f"app = FastAPI()\n\n"
        f'@app.post("/webhooks/{webhook_id}")\n'
        f"async def handle_{fn}(request: Request):\n"
        f"    payload = await request.json()\n"
        f'    event_type = payload.get("type")\n'
        f"    # process based on event type\n"
        f'    return {{"status": "received"}}\n'
        f"```\n\n"
        f"### Constraints\n"
        f"- Minimal changes \u2014 only add/change files needed for this integration.\n"
        f"- Match existing codebase patterns (naming, file structure, error handling).\n"
        f"- Return a 200 OK response to acknowledge receipt.\n\n"
        f"### Integration Checklist\n"
        f"Before writing code, verify:\n"
        f"1. Which module/service owns webhook handling in the codebase?\n"
        f"2. What routing and validation patterns does the project use?\n"
        f"3. Are there existing types/interfaces to extend?\n\n"
        f"Then implement the handler, export it, and confirm it compiles/passes lint."
    )
    return prompt


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def parse_frontmatter(content):
    """Return (dict, end_index_after_closing_dashes)."""
    if not content.startswith("---"):
        return {}, 0
    end = content.find("---", 3)
    if end == -1:
        return {}, 0
    fm_text = content[3:end].strip()
    result = {}
    for line in fm_text.split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            result[key.strip()] = value.strip().strip("'\"")
    return result, end + 3


# ---------------------------------------------------------------------------
# File processing
# ---------------------------------------------------------------------------

def _slug_from_filepath(filepath):
    """Derive a URL-safe slug from the MDX filename."""
    basename = os.path.splitext(os.path.basename(filepath))[0]
    return re.sub(r"[^a-z0-9\-]", "-", basename.lower())


def process_file(filepath, spec):
    """Read MDX, look up operation, generate accordion, write back."""
    with open(filepath, "r") as f:
        content = f.read()

    # strip old prompt section formats
    for pattern in [
        r'\n<div className="ai-prompt-box">\n<div className="ai-prompt-box-header">.*?````\n</div>\n',
        r'\n<Accordion title="Prompt for AI Agents">\n````\n.*?\n````\n</Accordion>\n',
        r'\n<Accordion title="Integration Prompt for AI Agents">\n````\n.*?\n````\n</Accordion>\n',
        r'\n<div className="ai-prompt-section">.*?</div>\n</div>\n',
        r'\n<div className="ai-prompt-section">.*?</Accordion>\n</div>\n',
        r'\n<Accordion title="Copy AI Integration Prompt">\n````\n.*?\n````\n</Accordion>\n',
    ]:
        content = re.sub(pattern, "", content, flags=re.DOTALL)

    fm, end_idx = parse_frontmatter(content)
    if not fm or "openapi" not in fm:
        return "skip"

    openapi_val = fm["openapi"]
    title = fm.get("title", "Unknown Endpoint")
    frontmatter = content[:end_idx]
    body = content[end_idx:]
    slug = _slug_from_filepath(filepath)

    if openapi_val.startswith("WEBHOOK"):
        webhook_id = openapi_val.split(" ", 1)[1].strip()
        op = spec.get("webhooks", {}).get(webhook_id, {}).get("post", {})
        if not op:
            prompt = (
                f"# Bluejay \u2014 Testing & Monitoring Platform for Conversational AI Agents\n\n"
                f"## Handle {title} \u2014 WEBHOOK\n\n"
                f"Set up a handler to receive and process this webhook payload.\n\n"
                f"### Webhook Details\n"
                f"- **Type:** Incoming Webhook\n"
                f"- **Payload Format:** JSON (POST)\n\n"
                f"### Constraints\n"
                f"- Minimal changes \u2014 only add/change files needed for this integration.\n"
                f"- Match existing codebase patterns.\n"
                f"- Return a 200 OK response to acknowledge receipt."
            )
        else:
            prompt = generate_webhook_prompt(spec, title, webhook_id, op)
    else:
        parts = openapi_val.split(" ", 1)
        if len(parts) != 2:
            return "skip"
        method, path = parts[0].strip(), parts[1].strip()
        op = spec.get("paths", {}).get(path, {}).get(method.lower(), {})
        if not op:
            return "warn"
        prompt = generate_endpoint_prompt(spec, title, method, path, op, docs_slug=slug)

    accordion = (
        f'\n<div className="ai-prompt-box">\n'
        f'<div className="ai-prompt-box-header">Integration Prompt for AI Agents</div>\n'
        f"````\n"
        f"{prompt}\n"
        f"````\n"
        f"</div>\n"
    )

    new_content = frontmatter + accordion + body

    with open(filepath, "w") as f:
        f.write(new_content)

    return "ok"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Loading OpenAPI spec...")
    spec = load_spec()
    print(f"  Paths: {len(spec.get('paths', {}))}")
    print(f"  Webhooks: {len(spec.get('webhooks', {}))}")
    print(f"  Schemas: {len(spec.get('components', {}).get('schemas', {}))}")

    endpoint_files = sorted(glob.glob(os.path.join(ENDPOINT_DIR, "*.mdx")))
    webhook_files = sorted(glob.glob(os.path.join(WEBHOOK_DIR, "*.mdx")))
    all_files = [f for f in endpoint_files + webhook_files if os.path.basename(f) not in SKIP_FILES]

    print(f"\nProcessing {len(all_files)} files...\n")

    counts = {"ok": 0, "skip": 0, "warn": 0}
    for filepath in all_files:
        basename = os.path.basename(filepath)
        result = process_file(filepath, spec)
        tag = {"ok": "  OK", "skip": "SKIP", "warn": "WARN"}.get(result, " ???")
        print(f"  [{tag}] {basename}")
        counts[result] = counts.get(result, 0) + 1

    print(f"\nDone. OK={counts['ok']}  SKIP={counts['skip']}  WARN={counts['warn']}")
    if counts["warn"] > 0:
        print("  (WARN = openapi path not found in spec)")
    return 0 if counts["warn"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
