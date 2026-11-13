# Bluejay Docs

## API reference pages

The parameter tables and examples on each page in `api-reference/endpoint/` come from the OpenAPI spec. After the API changes, run:

```bash
python3 scripts/generate_api_pages.py
python3 scripts/generate_cheat_sheet.py
```

The middleware repo runs both scripts on each push to `main` (`.github/workflows/docs-sync.yml` there). It opens one docs PR named "Sync API reference from middleware", with stub pages and nav entries for new routes and `deprecated: true` on deprecated routes. Merge it to publish.

The first script rewrites only the part of each page between the `GENERATED` markers, and the endpoint list of the API Playground page (`snippets/api-operations.jsx`). Edit the text above the markers by hand. The second script rebuilds the Cheat Sheet from the API sidebar in `docs.json`.

Routes listed in `scripts/api-ignore.txt` get no page. Delete a line to give that route a page on the next sync.
