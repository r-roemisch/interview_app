## Agent skills

### Issue tracker

Issues and specs live as local markdown files under `.scratch/<feature-slug>/` in this repo. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`, each used as-is as a `Status:` line in issue files. See `docs/agents/triage-labels.md`.

### README

`README.md` has two halves marked by HTML comments. The **owner section** is the user's own writing and stays exactly as they wrote it: when a change makes something in it stale, tell the user what to update. The **agent section** is yours; keep it in sync with the code.

### Domain docs

Single-context: `CONTEXT.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
