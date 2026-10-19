# AGENTS.md

This file provides guidance to coding agents working in this repository.

## Docs content

- The Integrations pages (`integrations/`) are the only place that lists the integrations and connection types. They change often, so other pages link to the first Integrations page, [Phone Number](/integrations/phone-number), instead of naming them. A page can still name the providers that one feature supports, for example which platforms can pull a workflow.
- Headings are sentence case. Page titles in frontmatter are Title Case, because the sidebar shows them.
- Capitalize product names: Bluejay AI, Bluejay as Code, Digital Human, Knowledge Base, Red Teaming, Metrics Lab, Self-Improve, and simulation type names. Generic nouns stay lowercase in running text: agent, simulation, custom metric, issue, alert, dashboard, conversation, trace, webhook, integration.
- App UI labels are bold and keep the app's exact capitalization.
- The first paragraph tells the reader what the page is for, clearly enough to decide in a second whether they are in the right place. That makes it short, such as "Use an alert with a [metric](/monitor/metrics) to catch failures on your production conversations." Leave mechanism and tips for the section where the reader needs them.
- The page header already shows the frontmatter `description`, so the first paragraph must not repeat it. Leave out lines about the page itself, such as "Open a section when you need it."
- Do not explain a button or field whose label already says what it does, such as "Click **Reset to default** to go back to the standard text." Clicks belong in the docs only as steps of a longer workflow, or when they carry something the screen does not show, such as a limit, a default, or a consequence.
- Leave out anything the reader sees on the screen: what a page shows, which section lists what, what opens when you click, where a transcript starts, where else a field can be set. Write only what the screen does not tell them: which action to take for their goal, and behavior they would not expect, such as "Bluejay never changes the status for you, so a **Resolved** issue that happens again stays **Resolved**."
- In tables, wrap a long identifier (12+ characters with `_`, `/`, or a dot between letters) in `<Code>` from `snippets/code.jsx` instead of backticks, so it breaks only at those separators. Write values that contain `<` or `>` as `<Code>{"MISSING_<PROVIDER>_INTEGRATION"}</Code>`.
- A page's overview video or demo goes right after the intro, before the first heading, so the page does not open with a wall of text. Media that shows one step stays in that step.
- Screenshots are in `images/`. An engineer who changes a pictured screen updates its screenshot in the same change. Capture from a test org, crop to the relevant area, and show no customer or internal names.
- A step never only sets a visible field, such as "Set **Number of calls** from 1 to 100." Keep setup to a few steps. Inside a step, add a bullet for a field only when it tells the reader something the label does not, such as a limit, a non-obvious effect, or a consequence. Never write a list that restates field labels, such as "**Agents**: the agents it applies to."

## PR conventions

PR title: `[ENG-(ticket #)] (fix if it's a fix) (title)`.

PR body is four sections, 2-3 sentences each:

- Background: what exists today and what prompted the change.
- Why: how this is a customer need.
- What: summary of the change.
- Notable: what a reviewer would otherwise miss.
