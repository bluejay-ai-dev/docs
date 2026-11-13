# AGENTS.md

This file provides guidance to coding agents working in this repository.

## Docs content

Write in plain, short sentences. Use the active voice. Do not use semicolons or em dashes.

### Page structure

- One page per feature. Split a page only when it goes over about 250 lines. Do not keep two pages that cover the same thing. Merge them and add a redirect from the old path.
- The first paragraph tells the reader what the page is for, clearly enough to decide in a second whether they are in the right place. That makes it short, such as "Use an alert with a [metric](/monitor/metrics) to catch failures on your production conversations." Leave mechanism and tips for the section where the reader needs them.
- The page header already shows the frontmatter `description`, so the first paragraph must not repeat it. Leave out lines about the page itself, such as "Open a section when you need it."
- A page `description` is a few words on what the page is for, such as "Master your tests with Digital Humans."
- A page's overview video or demo goes right after the intro, before the first heading, so the page does not open with a wall of text. Media that shows one step stays in that step.
- Keep setup to a few steps. A step never only sets a visible field, such as "Set **Number of calls** from 1 to 100." Inside a step, add a bullet for a field only when it tells the reader something the label does not, such as a limit, a non-obvious effect, or a consequence. Never write a list that restates field labels, such as "**Agents**: the agents it applies to."

### Wording

- Headings are sentence case. Page titles in frontmatter are Title Case, because the sidebar shows them.
- Capitalize product names: Bluejay AI, Bluejay as Code, Digital Human, Knowledge Base, Red Teaming, Metrics Lab, Self-Improve, and simulation type names. Generic nouns stay lowercase in running text: agent, simulation, custom metric, issue, alert, dashboard, conversation, trace, webhook, integration.
- App UI labels are bold and keep the app's exact capitalization. A page named after a feature uses the app's label for it.
- The `integrations/` folder holds the agent connection pages (Connect Your Agent). The `native-integrations/` folder, the CI/CD tab, holds GitHub, GitLab and Azure DevOps.
- The agent connection pages (`integrations/`) are the only place that lists the integrations and connection types. They change often, so other pages link to the first Integrations page, [Connect Your Agent](/integrations/overview), instead of naming them. A page can still name the providers that one feature supports, for example which platforms can pull a workflow. The API reference can also list connection types with their request fields, as Add Agent does, because API users need the field names.

### What to leave out

- Do not explain a button or field whose label already says what it does, such as "Click **Reset to default** to go back to the standard text." Clicks belong in the docs only as steps of a longer workflow, or when they carry something the screen does not show, such as a limit, a default, or a consequence.
- Leave out anything the reader sees on the screen: what a page shows, which section lists what, what opens when you click, where a transcript starts, where else a field can be set. Write only what the screen does not tell them: which action to take for their goal, and behavior they would not expect, such as "Bluejay never changes the status for you, so a **Resolved** issue that happens again stays **Resolved**."
- Do not repeat content from another page. Link to it.

### Nav and sidebar

- Every non-API-reference page in the sidebar has an `icon` in frontmatter. Reuse a Font Awesome name already in `docs.json` when it fits.
- Reference pages, such as statuses, limits, and field tables, sit at the bottom of their nav group, after the guides.
- A `/v1` endpoint that has a `/v2` starts with a `<Note>` that says which to use for new integrations and why. In the sidebar, each `/v2` sits directly above its `/v1`.
- When you move, rename, or delete a page, add a redirect from the old path and fix every internal link.

### Media

- Screenshots are in `images/`. An engineer who changes a pictured screen updates its screenshot in the same change. Capture from a test org, crop to the relevant area, and show no customer or internal names.

### Tables

- In tables, wrap a long identifier (12+ characters with `_`, `/`, or a dot between letters) in `<Code>` from `snippets/code.jsx` instead of backticks, so it breaks only at those separators. Write values that contain `<` or `>` as `<Code>{"MISSING_<PROVIDER>_INTEGRATION"}</Code>`.
- Put one value in each cell.

## PR conventions

PR title: `[ENG-(ticket #)] (fix if it's a fix) (title)`.

PR body is four sections, 2-3 sentences each:

- Background: what exists today and what prompted the change.
- Why: how this is a customer need.
- What: summary of the change.
- Notable: what a reviewer would otherwise miss.
