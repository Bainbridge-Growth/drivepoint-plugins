# Context templates

Starting files for a company's context library and for each user's personal
context. webapp-server copies these when a company is set up, Neo's "New
file" button starts from them, and the drivepoint-customers importer fills
them in.

The rules for writing context live in the `context-guide` common skill.
`context-contract.json` holds the machine-readable limits, which
`scripts/check_context_contract.py` checks here in CI and webapp-server checks
on every `write_context` call.

```
organization/
  profile.md               always in the prompt
  guidance.md              always in the prompt
  security.md              always in the prompt
  context/business.md      in the index; read on demand
  context/data-sources.md
  context/model.md
  context/metrics.md
  context/glossary.md
  context/team.md
  skills/_template/SKILL.md
personal/
  preferences.md           always in the prompt
  context/notes.md
```

Placeholders are written as `<…>`, and template dates as `YYYY-MM-DD`. A saved
file must replace both.
