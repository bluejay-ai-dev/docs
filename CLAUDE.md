# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Branch and PR conventions

Work starts from a Linear ticket in the Engineering team (ENG-...). Branch off `dev` (or `main` if this repo has no `dev`) and name the branch `kk-ENG-(ticket #)-(descriptive_feature_name)`.

PR title: `[ENG-(ticket #)] (fix if it's a fix) (title)`.

PR body is exactly four sections, 2-3 sentences each, hard cap:

- Background: what exists today and what prompted the change.
- Why: how this is a customer need.
- What: summary of the change.
- Notable: what a reviewer would otherwise miss.

Cut anything that does not change how someone reviews or merges it. Minimal formatting, no bold or italics, bullets only for real lists.
