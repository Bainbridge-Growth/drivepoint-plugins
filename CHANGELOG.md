# Changelog

## mcp-server 0.2.0 — Neo release (unreleased)

Ships with the Neo context release. Merge only together with the
webapp-server change that registers the context MCP tools.

- System prompt: new "Company and personal context" section covering what is
  already in the prompt, reading on demand, `company:` / `me:` skills,
  precedence, and confirmed write-back.
- New common skill `context-guide`: what goes where, frontmatter, size
  limits, and what never to save.
- New `context-templates/` with `context-contract.json`, checked in CI by
  `scripts/check_context_contract.py`.
- Tool-name pin: adds `list_context`, `read_context`, `write_context`, and
  `get_context_history`, and the `write` verb.
