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

### PUBLIC

```bash
/plugin marketplace add <org>/drivepoint-plugins
/plugin install smartmodel@drivepoint
```

Replace `<org>` with your GitHub org (for example `Bainbridge-Growth`). The marketplace registry name is **`drivepoint`** (set in this repo’s `.claude-plugin/marketplace.json`). The GitHub repo is **`Bainbridge-Growth/drivepoint-plugins`**.

**Private repo + Claude org / Desktop:** The `smartmodel` entry uses a **relative** plugin source (`"./"`) so the catalog resolves inside this same GitHub repo after clone — the same pattern as `drivepoint-internal-plugins`. A nested `"source": { "github", "repo": "…/drivepoint-plugins" }` forces a second unauthenticated GitHub lookup and fails validation for private repos (“repository not found … make sure the repository is public”).

### PRIVATE

```bash
/plugin marketplace add <org>/drivepoint-internal-plugins
/plugin install dp-design@drivepoint-internal
```

The internal marketplace registry name is **`drivepoint-internal`**. Plugin ids (for example `dp-design`) come from each plugin’s `.claude-plugin/plugin.json` in the internal repo.

**Migrating from older installs:** If you used the `@drivepoint-smartmodel` marketplace suffix, remove that marketplace entry and re-add with `<org>/drivepoint-plugins`, then `smartmodel@drivepoint`. After GitHub renames the repo, run `git remote set-url origin https://github.com/<org>/drivepoint-plugins.git` in your local clone (rename the worktree folder to `drivepoint-plugins` when convenient). The Claude **plugin** id is `smartmodel`; the main **skill** for the protocol spec remains `smartmodel-protocol` (invoke with `/skill smartmodel-protocol`).

## Usage
Install the `smartmodel` plugin once. When working with a SmartModel workbook, the `smartmodel-protocol` skill is the canonical protocol entry point. Invoke it explicitly with `/skill smartmodel-protocol` when needed.

## Plugin Structure
```
drivepoint-plugins/
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
    summarize-model/SKILL.md        ← Model Ops
    interrogate-model/SKILL.md
    audit-model/SKILL.md
    clean-model/SKILL.md
    optimize-model/SKILL.md
    compare-scenarios/SKILL.md      ← Scenarios
  trial/
    welcome.md                       ← guided trial experience for prospects
  .mcp.json                          ← MCP stub (ready for future server integration)
  README.md
```

Each skill is a `<name>/SKILL.md` directory following the Claude plugin spec. The logical groupings (Builders, Analysis, Model Ops, Scenarios) are documented above but the actual directory structure is flat — all skills are direct children of `skills/`.

## Try Drivepoint (Trial Experience)

Share this link with prospects to launch a guided Drivepoint trial inside Claude:

```
claude://claude.ai/new?q=Read%20https%3A%2F%2Fraw.githubusercontent.com%2FBainbridge-Growth%2Fdrivepoint-plugins%2Fmain%2Ftrial%2Fwelcome.md%20and%20follow%20the%20instructions%20inside%20it%20exactly.
```

The link opens a new Claude conversation pre-filled with a prompt that loads `trial/welcome.md`. Claude reads the file, then runs a guided trial experience using a sample CPG brand (Oatwave). The prospect picks from five analysis paths (variance, cohort/margins, inventory/demand planning, investor readiness, SKU rationalization) and sees Drivepoint-quality output on sample data, with a CTA to connect their real data.

No install required. Works on claude.ai, Claude Desktop, and Claude mobile.

**To update the trial experience**, edit `trial/welcome.md` and push to main. The link never changes.

## The Protocol
The canonical SmartModel Protocol v6.0 specification lives at `skills/smartmodel-protocol/SKILL.md` — this is both the protocol spec and the Claude plugin entry point.

## Related Repos
| Repo | Purpose |
|------|---------|
| [drivepoint-smartmodel-templates](https://github.com/Bainbridge-Growth/drivepoint-smartmodel-templates) | Template content library (skills, imports, xlsx artifacts) |
| [drivepoint-smartmodel-utils](https://github.com/Bainbridge-Growth/drivepoint-smartmodel-utils) | Python tools for conversion, generation, validation |
