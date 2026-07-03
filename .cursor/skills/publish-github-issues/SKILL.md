---
name: publish-github-issues
description: >-
  Publish local issue drafts from docs/issues/ manifest to GitHub using gh CLI
  for 3urega/femturisme. Use when uploading issues, publishing a batch, or
  after plan-to-issues.
---

# Publish GitHub Issues

Repository: **`3urega/femturisme`**

All `gh` commands **must** include `--repo 3urega/femturisme`.

**Issue lifecycle:** [plan-to-issues](../plan-to-issues/SKILL.md) → **publish-github-issues** (this skill) → [kanban-board](../kanban-board/SKILL.md)

---

## Prerequisites

- GitHub CLI (`gh`) installed and authenticated (`gh auth status`)
- Draft files exist under `docs/issues/`
- Manifest JSON ready (see [docs/issues/README.md](../../../docs/issues/README.md))

---

## Commands

List existing open issues (avoid duplicates):

```bash
gh issue list --repo 3urega/femturisme --limit 50
```

Create one issue:

```bash
gh issue create --repo 3urega/femturisme \
  --title "Title here" \
  --body-file docs/issues/01-experiences-repository.md \
  --label "enhancement" --label "fase-3" --label "mysql"
```

View created issue:

```bash
gh issue view <number> --repo 3urega/femturisme
```

---

## Workflow — publish a manifest batch

### 1. Validate before publish

For each entry in `manifest.*.json`:

- [ ] `"repo"` is `"3urega/femturisme"` (or matches this project)
- [ ] `bodyFile` exists and is non-empty
- [ ] Title is unique vs `gh issue list --search "in:title <title>"`
- [ ] Labels exist on repo (create if user approves: `gh label create …`)
- [ ] `sourceDoc` referenced in manifest is valid

Read manifest:

```bash
# Example — adjust filename
cat docs/issues/manifest.fase3-mysql.json
```

### 2. Publish in dependency order

Sort issues by draft number / dependencies (foundational repos before dependents).

For each issue **not yet published** (no `githubNumber` in manifest):

```bash
gh issue create --repo 3urega/femturisme \
  --title "<title from manifest>" \
  --body-file "<bodyFile>" \
  --label "<label1>" --label "<label2>"
```

Capture the returned issue number from stdout (e.g. `https://github.com/3urega/femturisme/issues/42` → `42`).

### 3. Update manifest

Add to each published entry:

```json
{
  "title": "...",
  "bodyFile": "docs/issues/01-experiences-repository.md",
  "labels": ["fase-3", "mysql"],
  "githubNumber": 42,
  "publishedAt": "2026-07-03"
}
```

If bodies reference other draft issues by number, update cross-links to `#42` GitHub numbers after publish.

### 4. Report to user

Table:

| GitHub # | Title | URL |
|----------|-------|-----|
| #42 | … | https://github.com/3urega/femturisme/issues/42 |

Suggest next step: `/kanban-board 42` or list open issues.

---

## Single issue (ad hoc)

When user asks to create one issue without manifest:

1. Write or confirm body file under `docs/issues/`
2. Run `gh issue create` as above
3. Optionally append to an existing manifest or create minimal manifest for traceability

---

## Body file enhancements before publish

Ensure each body includes:

- **Objectiu** and **Criteris d'acceptació** (checkboxes)
- **Fora d'abast**
- **Referències** to project docs (relative paths OK)
- **Verificació** — concrete commands:

```bash
pytest tests/integration/sql/test_experiences.py -v
curl -s http://127.0.0.1:5010/health
```

---

## Error handling

| Error | Action |
|-------|--------|
| `gh: Not authenticated` | Ask user to run `gh auth login` |
| Duplicate title | Skip or ask user to rename |
| Label missing | `gh label create "fase-3" --repo 3urega/femturisme --color "0E8A16"` |
| bodyFile not found | Stop batch; fix path in manifest |

**Never** publish issues containing secrets (`.env`, API keys, passwords).

---

## Do not

- Close issues here — use [kanban-board](../kanban-board/SKILL.md)
- Delete local drafts on publish — keep until issue is **closed** and implemented
- Force-push or modify git config

---

## Related

- [plan-to-issues](../plan-to-issues/SKILL.md)
- [kanban-board](../kanban-board/SKILL.md)
- [docs/issues/README.md](../../../docs/issues/README.md)
