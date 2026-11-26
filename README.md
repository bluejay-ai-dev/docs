# Bluejay Docs

SaturnDocs publishes the docs from the `site/` folder. Each push to `main` starts a build.

## Layout

- `site/docs.json` holds the navigation, the redirects and the site settings.
- `site/pages/` holds the pages. The file path is the page address: `site/pages/monitor/alerts.mdx` is `/monitor/alerts`.
- `site/components/` holds the components that pages use, such as `FieldTable` and `Code`.
- `site/public/` holds the images, the videos, the logo and `theme.css`.

Before you push, check the site:

```bash
npx saturndocs@latest check site
```

## Mintlify files

The files outside `site/` and `scripts/` are the Mintlify version of the docs. Mintlify serves docs.getbluejay.ai from them until the domain moves to SaturnDocs. `.mintignore` keeps `site/` out of the Mintlify build. Do not edit the Mintlify files. A later pull request removes them.

## API reference pages

The parameter tables and examples on each page in `site/pages/api-reference/endpoint/` come from the OpenAPI spec. After the API changes, run:

```bash
python3 scripts/generate_api_pages.py
python3 scripts/generate_cheat_sheet.py
```

The middleware repo runs both scripts on each push to `main` (`.github/workflows/docs-sync.yml` there). It pushes the regenerated files straight to docs `main`, with stub pages and nav entries for new routes and `deprecated: true` on deprecated routes. Add the intro sentence to a new page by hand afterward.

The first script rewrites only the part of each page between the `GENERATED` markers. It also writes the sidebar entries in `site/docs.json`, the endpoint list of the API Playground page (`site/components/operations.json`), and the endpoint title rules between the `GENERATED: endpoint titles` markers in `site/public/theme.css`. Edit the text above the markers by hand. The second script rebuilds the Cheat Sheet from the API sidebar in `site/docs.json`.

Routes listed in `scripts/api-ignore.txt` get no page. Routes with an `internal`, `admin`, `health`, `.well-known` or `ping` path segment, a `bbb` path segment, or an internal token header never get one. Delete a line to give that route a page on the next sync.
