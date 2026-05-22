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
    plugin.json                      ← plugin manifest
    marketplace.json                 ← marketplace registry entry
  skills/
    smartmodel-protocol/SKILL.md    ← canonical protocol specification (plugin entry point)
    build-schedule/SKILL.md         ← Builders
    build-report/SKILL.md
    create-scenario/SKILL.md
    variance-analysis/SKILL.md      ← Analysis
    margin-analysis/SKILL.md
    sku-rationalization/SKILL.md
    cohort-analysis/SKILL.md
    investor-readiness-analysis/SKILL.md
    product-cost-analysis/SKILL.md
    marketing-efficiency-analysis/SKILL.md
    inventory-analysis/SKILL.md
    trade-spend-analysis/SKILL.md
    monthly-report/SKILL.md         ← Monthly Report
    price-change-analysis/SKILL.md
    summarize-model/SKILL.md        ← Model Ops
    interrogate-model/SKILL.md
    audit-model/SKILL.md
    clean-model/SKILL.md
    optimize-model/SKILL.md
    qa-financials/SKILL.md          ← Finance QA
    compare-scenarios/SKILL.md      ← Scenarios
  .mcp.json                          ← MCP stub (ready for future server integration)
  README.md
```

Each skill is a `<name>/SKILL.md` directory following the Claude plugin spec. The logical groupings (Builders, Analysis, Model Ops, Scenarios) are documented above but the actual directory structure is flat — all skills are direct children of `skills/`.

## The Protocol
The canonical SmartModel Protocol v6.0 specification lives at `skills/smartmodel-protocol/SKILL.md` — this is both the protocol spec and the Claude plugin entry point.

## Related Repos
| Repo | Purpose |
|------|---------|
| [drivepoint-smartmodel-templates](https://github.com/Bainbridge-Growth/drivepoint-smartmodel-templates) | Template content library (skills, imports, xlsx artifacts) |
| [drivepoint-smartmodel-utils](https://github.com/Bainbridge-Growth/drivepoint-smartmodel-utils) | Python tools for conversion, generation, validation |
