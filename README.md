# SmartModel Protocol — Claude Plugin

**Version**: 1.0.0
**Published by**: Drivepoint (drivepoint.io)

Teaches any Claude session the SmartModel Protocol v6.0 grammar — the AI-readable standard for Drivepoint Excel financial models.

---

## What This Plugin Does

When installed, this plugin gives Claude the ability to:
- Navigate any SmartModel workbook by reading its sheet structure, tab colors, and row grammar
- Identify input cells (Key Driver) vs. calculated results (Key Result) via column A storage markers
- Read and interpret machine-readable identifiers in column B
- Understand the date spine, period types, metadata block, settings block, and data sections
- Consult the imports system to know what external data the model needs

---

## Install

```bash
/plugin marketplace add Bainbridge-Growth/drivepoint-smartmodel-plugin
/plugin install smartmodel-protocol@drivepoint-smartmodel
```

---

## Usage

Once installed, the `smartmodel-protocol` skill loads automatically when you work with a SmartModel workbook. You can also invoke it explicitly:

```
/skill smartmodel-protocol
```

Then open or share a SmartModel `.xlsx` file and ask Claude questions about it.

---

## Plugin Structure

```
drivepoint-smartmodel-plugin/
  .claude-plugin/
    plugin.json          ← plugin manifest
    marketplace.json     ← marketplace registry entry
  skills/
    smartmodel-protocol/
      SKILL.md           ← protocol grammar (plugin entry point)
  .mcp.json              ← MCP stub (ready for future server integration)
  README.md
```

---

## The Skill

The `SKILL.md` at `skills/smartmodel-protocol/SKILL.md` contains the full SmartModel Protocol v6.0 grammar. It is identical in content to the canonical protocol skill hosted at:

```
https://raw.githubusercontent.com/Bainbridge-Growth/drivepoint-smartmodel-protocol/main/protocol/v6.0/smartmodel-skill.md
```

The protocol repo is the authoritative source. This plugin repo packages it for Claude plugin distribution.

---

## Related Repos

| Repo | Purpose |
|------|---------|
| [drivepoint-smartmodel-protocol](https://github.com/Bainbridge-Growth/drivepoint-smartmodel-protocol) | Protocol spec, grammar skill (canonical source) |
| [drivepoint-smartmodel-templates](https://github.com/Bainbridge-Growth/drivepoint-smartmodel-templates) | SmartModel workbook templates and generator tools |
