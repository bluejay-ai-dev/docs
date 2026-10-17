# AGENTS.md

This file provides guidance to coding agents working in this repository.

## Docs content

- The Integrations pages (`integrations/`) are the only place that lists the integrations and connection types. They change often, so other pages link to the [Integrations overview](/integrations/overview) instead of naming them. A page can still name the providers that one feature supports, for example which platforms can pull a workflow.
- Headings are sentence case. Page titles in frontmatter are Title Case, because the sidebar shows them.
- Capitalize product names: Bluejay AI, Bluejay as Code, Digital Human, Knowledge Base, Red Teaming, Metrics Lab, Self-Improve, and simulation type names. Generic nouns stay lowercase in running text: agent, simulation, custom metric, issue, alert, dashboard, conversation, trace, webhook, integration.
- App UI labels are bold and keep the app's exact capitalization.
- Do not explain a button or field whose label already says what it does, such as "Click **Reset to default** to go back to the standard text." Clicks belong in the docs only as steps of a longer workflow, or when they carry something the screen does not show, such as a limit, a default, or a consequence.

## PR conventions

PR title: `[ENG-(ticket #)] (fix if it's a fix) (title)`.

PR body is four sections, 2-3 sentences each:

- Background: what exists today and what prompted the change.
- Why: how this is a customer need.
- What: summary of the change.
- Notable: what a reviewer would otherwise miss.
