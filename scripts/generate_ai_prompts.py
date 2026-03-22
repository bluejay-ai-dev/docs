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


def build_params_table(header_params, body_schema):
    """Build a single unified parameter table."""
    rows = []
    if header_params:
        for p in header_params:
            desc = p["description"].replace("\n", " ").replace("|", "\\|")
            rows.append(
                f"| {p['name']} | {p['location']} | {p['type']} "
                f"| {p['required']} | {desc} |"
            )

    if body_schema and "properties" in body_schema:
        required = set(body_schema.get("required", []))
        for pn, ps in body_schema["properties"].items():
            ts = get_type_str(ps)
            req = "yes" if pn in required else "no"
            desc = (ps.get("description") or "").replace("\n", " ").replace("|", "\\|")
            if "default" in ps and ps["default"] is not None:
                desc += f" (default: {ps['default']})"
            rows.append(f"| {pn} | body | {ts} | {req} | {desc} |")

    if not rows:
        return "No parameters required."

    header = (
        "| Name | Location | Type | Required | Description |\n"
        "|------|----------|------|----------|-------------|"
    )
    return header + "\n" + "\n".join(rows)


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

def generate_endpoint_prompt(spec, title, method, path, operation):
    method = method.upper()

    params = extract_params(spec, operation)
    body_schema = extract_body_schema(spec, operation)
    resp_code, resp_schema, resp_desc = extract_response(spec, operation)
    error_codes = extract_error_codes(operation)

    params_table = build_params_table(params, body_schema)

    body_section = ""
    if body_schema:
        example = schema_to_example(body_schema)
        if example:
            body_json = json.dumps(example, indent=2)
            body_section = f"\n\n## Request Body Schema\n```json\n{body_json}\n```"

    if resp_schema:
        resp_example = schema_to_example(resp_schema)
        if resp_example:
            resp_json = json.dumps(resp_example, indent=2)
            resp_section = f"\n\n## Response\n- **Success ({resp_code}):**\n```json\n{resp_json}\n```"
        else:
            resp_section = f"\n\n## Response\n- **Success ({resp_code}):** {resp_desc}"
    elif resp_code == "204":
        resp_section = f"\n\n## Response\n- **Success ({resp_code}):** No response body"
    else:
        resp_section = f"\n\n## Response\n- **Success ({resp_code}):** {resp_desc}"

    error_line = ""
    if error_codes:
        error_line = "\n- **Key error codes:** " + "; ".join(error_codes[:3])

    ct_line = ""
    if body_schema:
        ct_line = "\n- **Content-Type:** application/json"

    openapi_type_map = {"integer": "int", "number": "float", "boolean": "bool"}
    param_types = {}
    for p in params:
        if p["location"] == "path":
            raw = p["type"].split()[0].strip("()")
            param_types[p["name"]] = openapi_type_map.get(raw, "str")

    few_shot = generate_few_shot(method, path, title, body_schema is not None, param_types)

    prompt = (
        f"# Integrate {title} — {method} {path}\n\n"
        f"**You are a senior backend engineer. Your task: integrate the endpoint below "
        f"into the existing codebase with minimal, surgical changes. Do not refactor, "
        f"rename, or restructure anything beyond what is required for this integration.**\n\n"
        f"## Endpoint Details\n"
        f"- **Method:** {method}\n"
        f"- **URL:** `{BASE_URL}{path}`\n"
        f"- **Auth:** API Key via `X-API-Key` header{ct_line}\n\n"
        f"## Parameters\n"
        f"{params_table}"
        f"{body_section}"
        f"{resp_section}"
        f"{error_line}\n\n"
        f"## Integration Instructions\n"
        f"1. Create or locate the appropriate service/module for this API domain.\n"
        f"2. Implement the API call using the project's existing HTTP client and patterns.\n"
        f"3. Include proper error handling for the documented error codes.\n"
        f"4. Add TypeScript types / interfaces for request params and response shape (if TS project).\n"
        f"5. Export the function so it's consumable by the rest of the codebase.\n\n"
        f"## Few-Shot Example\n{few_shot}\n\n"
        f"## Constraints\n"
        f"- **Be concise.** Only add/change files directly needed for this integration.\n"
        f"- **Match existing patterns** in the codebase (naming, file structure, error handling).\n"
        f"- **Do not** install new dependencies unless absolutely required.\n"
        f"- **Do not** modify unrelated files.\n\n"
        f"**Reminder: Integrate this single endpoint fully and correctly. "
        f"Minimal diff, maximum correctness.**"
    )
    return prompt


def generate_webhook_prompt(spec, title, webhook_id, operation):
    description = operation.get("description", "")

    rb = operation.get("requestBody", {})
    raw_schema = rb.get("content", {}).get("application/json", {}).get("schema", {})
    resolved = resolve_schema(spec, raw_schema) if raw_schema else None

    # Payload table + example sections
    payload_table_lines = []
    payload_examples = ""

    if resolved and "oneOf" in resolved:
        discriminator = resolved.get("discriminator", {})
        disc_prop = discriminator.get("propertyName", "type")
        mapping = discriminator.get("mapping", {})

        payload_examples = (
            f"\n\n## Payload Schema\n"
            f"This webhook sends different payload types, discriminated by the "
            f"`{disc_prop}` field:\n"
        )
        payload_table_lines.append("| Name | Type | Required | Description |")
        payload_table_lines.append("|------|------|----------|-------------|")

        for vtype, vref in mapping.items():
            vs = resolve_ref(spec, vref)
            payload_table_lines.append(f"| **Variant: `{vtype}`** | | | |")
            req_fields = set(vs.get("required", []))
            for pn, ps in vs.get("properties", {}).items():
                ts = get_type_str(ps)
                rq = "yes" if pn in req_fields else "no"
                d = (ps.get("description") or "").replace("\n", " ").replace("|", "\\|")
                payload_table_lines.append(f"| {pn} | {ts} | {rq} | {d} |")

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
            ts = get_type_str(ps)
            rq = "yes" if pn in req_fields else "no"
            d = (ps.get("description") or "").replace("\n", " ").replace("|", "\\|")
            payload_table_lines.append(f"| {pn} | {ts} | {rq} | {d} |")
        example = schema_to_example(resolved)
        if example:
            ej = json.dumps(example, indent=2)
            payload_examples = f"\n\n## Payload Schema\n```json\n{ej}\n```"

    payload_table = "\n".join(payload_table_lines) if payload_table_lines else "See payload examples below."

    fn = sanitize_func_name(title)

    prompt = (
        f"# Handle {title} — WEBHOOK\n\n"
        f"**You are a senior backend engineer. Your task: set up a handler to receive and "
        f"process this webhook payload in the existing codebase with minimal, surgical "
        f"changes. Do not refactor, rename, or restructure anything beyond what is "
        f"required for this integration.**\n\n"
        f"## Webhook Details\n"
        f"- **Type:** Incoming Webhook\n"
        f"- **Payload Format:** JSON (POST)\n"
        f"- **Description:** {description}\n\n"
        f"## Payload Fields\n"
        f"{payload_table}"
        f"{payload_examples}\n\n"
        f"## Integration Instructions\n"
        f"1. Create or locate the appropriate webhook handler module.\n"
        f"2. Implement a route/endpoint to receive the webhook POST request.\n"
        f"3. Validate the incoming payload structure.\n"
        f"4. Process the webhook data according to business logic.\n"
        f"5. Return an appropriate response (200 OK) to acknowledge receipt.\n\n"
        f"## Few-Shot Example\n"
        f"**Flask webhook handler:**\n"
        f"```python\n"
        f"from flask import Flask, request, jsonify\n\n"
        f"app = Flask(__name__)\n\n"
        f'@app.route("/webhooks/{webhook_id}", methods=["POST"])\n'
        f"def handle_{fn}():\n"
        f"    payload = request.get_json()\n"
        f"    if not payload:\n"
        f'        return jsonify({{"error": "Invalid payload"}}), 400\n'
        f'    event_type = payload.get("type")\n'
        f"    # Process based on event type\n"
        f"    # ...\n"
        f'    return jsonify({{"status": "received"}}), 200\n'
        f"```\n\n"
        f"**FastAPI webhook handler:**\n"
        f"```python\n"
        f"from fastapi import FastAPI, Request\n\n"
        f"app = FastAPI()\n\n"
        f'@app.post("/webhooks/{webhook_id}")\n'
        f"async def handle_{fn}(request: Request):\n"
        f"    payload = await request.json()\n"
        f'    event_type = payload.get("type")\n'
        f"    # Process based on event type\n"
        f"    # ...\n"
        f'    return {{"status": "received"}}\n'
        f"```\n\n"
        f"## Constraints\n"
        f"- **Be concise.** Only add/change files directly needed for this integration.\n"
        f"- **Match existing patterns** in the codebase (naming, file structure, error handling).\n"
        f"- **Do not** install new dependencies unless absolutely required.\n"
        f"- **Do not** modify unrelated files.\n\n"
        f"**Reminder: Set up this webhook handler fully and correctly. "
        f"Minimal diff, maximum correctness.**"
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

def process_file(filepath, spec):
    """Read MDX, look up operation, generate accordion, write back."""
    with open(filepath, "r") as f:
        content = f.read()

    if '<Accordion title="Copy AI Integration Prompt">' in content:
        content = re.sub(
            r'\n<Accordion title="Copy AI Integration Prompt">\n````\n.*?\n````\n</Accordion>\n',
            "",
            content,
            flags=re.DOTALL,
        )

    fm, end_idx = parse_frontmatter(content)
    if not fm or "openapi" not in fm:
        return "skip"

    openapi_val = fm["openapi"]
    title = fm.get("title", "Unknown Endpoint")
    frontmatter = content[:end_idx]
    body = content[end_idx:]

    if openapi_val.startswith("WEBHOOK"):
        webhook_id = openapi_val.split(" ", 1)[1].strip()
        op = spec.get("webhooks", {}).get(webhook_id, {}).get("post", {})
        if not op:
            prompt = (
                f"# Handle {title} — WEBHOOK\n\n"
                f"**You are a senior backend engineer. Your task: set up a handler to "
                f"receive and process this webhook payload with minimal, surgical changes.**\n\n"
                f"## Webhook Details\n"
                f"- **Type:** Incoming Webhook\n"
                f"- **Payload Format:** JSON (POST)\n\n"
                f"## Integration Instructions\n"
                f"1. Create or locate the appropriate webhook handler module.\n"
                f"2. Implement a route/endpoint to receive the webhook POST request.\n"
                f"3. Validate the incoming payload structure.\n"
                f"4. Return a 200 OK response to acknowledge receipt.\n\n"
                f"**Reminder: Set up this webhook handler fully and correctly. "
                f"Minimal diff, maximum correctness.**"
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
        prompt = generate_endpoint_prompt(spec, title, method, path, op)

    accordion = (
        '\n<Accordion title="Copy AI Integration Prompt">\n'
        "````\n"
        f"{prompt}\n"
        "````\n"
        "</Accordion>\n"
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
