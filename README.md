# Bluejay Docs

## API reference pages

The parameter tables and examples on each page in `api-reference/endpoint/` come from the OpenAPI spec. After the API changes, run:

```bash
python3 scripts/generate_api_pages.py
python3 scripts/generate_cheat_sheet.py
```

The first script rewrites only the part of each page between the `GENERATED` markers, and the endpoint list of the Try it page (`snippets/api-operations.jsx`). Edit the text above the markers by hand. The second script rebuilds the Cheat Sheet from the API sidebar in `docs.json`.
