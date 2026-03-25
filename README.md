# SmartModel Protocol — Claude Plugin

**Version**: 1.0.0
**Published by**: Drivepoint (drivepoint.io)

Teaches any Claude session the SmartModel Protocol v6.0 grammar — the AI-readable standard for Drivepoint Excel financial models. This repo is the **canonical home** of the SmartModel Protocol specification.

## What This Plugin Does
- Navigate any SmartModel workbook by reading sheet structure, tab colors, and row grammar
- Identify input cells (Key Driver) vs. calculated results (Key Result) via column A storage markers
- Read and interpret machine-readable identifiers in column B
- Understand date spine, period types, metadata block, settings block, and data sections
- Consult the imports system to know what external data the model needs

## Install
```bash
/plugin marketplace add Bainbridge-Growth/drivepoint-smartmodel-plugin
/plugin install smartmodel-protocol@drivepoint-smartmodel
```

## Usage
Once installed, the `smartmodel-protocol` skill loads automatically when working with a SmartModel workbook. Can also invoke explicitly: `/skill smartmodel-protocol`

## Plugin Structure
```
drivepoint-smartmodel-plugin/
  .claude-plugin/
    plugin.json          ← plugin manifest
    marketplace.json     ← marketplace registry entry
  protocol/
    v6.0/
      smartmodel-spec.md ← canonical protocol specification
  skills/
    smartmodel-protocol/
      SKILL.md           ← protocol grammar (plugin entry point)
  .mcp.json              ← MCP stub (ready for future server integration)
  README.md
```

## The Protocol
The canonical SmartModel Protocol v6.0 specification lives at `protocol/v6.0/smartmodel-spec.md`. The `SKILL.md` in `skills/smartmodel-protocol/` contains the same content, packaged as a Claude plugin skill entry point.

## Related Repos
| Repo | Purpose |
|------|---------|
| [drivepoint-smartmodel-templates](https://github.com/Bainbridge-Growth/drivepoint-smartmodel-templates) | Template content library (skills, imports, xlsx artifacts) |
| [drivepoint-smartmodel-utils](https://github.com/Bainbridge-Growth/drivepoint-smartmodel-utils) | Python tools for conversion, generation, validation |
