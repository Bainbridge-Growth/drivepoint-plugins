# Drivepoint Plugins — Claude Marketplace

**Published by**: Drivepoint (drivepoint.io)

This repository is the **Drivepoint plugin marketplace** for Claude. It hosts
Drivepoint's Claude products as separate, independently-installable plugins.

| Plugin | What it does | Version |
|--------|--------------|---------|
| **`smartmodel`** | SmartModel Protocol v6.0 — the AI-readable grammar for Drivepoint Excel financial models, plus the full SmartModel skill library (builders, analysis, model ops, scenarios). This repo is the **canonical home** of the SmartModel Protocol specification. | 1.1.0 |
| **`mcp-server`** | The Drivepoint MCP server — connects Claude to a brand's Drivepoint analytics data (read-only, BigQuery-backed marts, skills, and plans). | 0.1.0 |

## Install

```bash
/plugin marketplace add <org>/drivepoint-plugins
/plugin install smartmodel@drivepoint     # SmartModel Protocol + skills
/plugin install mcp-server@drivepoint      # Drivepoint MCP server
```

Replace `<org>` with your GitHub org (for example `Bainbridge-Growth`). The
marketplace registry name is **`drivepoint`** (set in this repo's
`.claude-plugin/marketplace.json`). The GitHub repo is
**`Bainbridge-Growth/drivepoint-plugins`**.

**Private repo + Claude org / Desktop:** each plugin entry uses a **relative**
subdirectory source (`"./plugins/smartmodel"`, `"./plugins/mcp-server"`) so the
catalog resolves inside this same GitHub repo after clone. A nested
`"source": { "github", "repo": "…/drivepoint-plugins" }` forces a second
unauthenticated GitHub lookup and fails validation for private repos
("repository not found … make sure the repository is public").

**Internal plugins** live in a separate repo:

```bash
/plugin marketplace add <org>/drivepoint-internal-plugins
/plugin install dp-design@drivepoint-internal
```

The internal marketplace registry name is **`drivepoint-internal`**. Plugin ids
(for example `dp-design`) come from each plugin's `.claude-plugin/plugin.json`
in the internal repo.

## Repository Structure

```
drivepoint-plugins/                          ← marketplace root
  .claude-plugin/
    marketplace.json                         ← registry: lists both plugins (relative sources)
  plugins/
    smartmodel/                              ← SmartModel plugin
      .claude-plugin/plugin.json
      skills/
        smartmodel-protocol/SKILL.md         ← canonical protocol spec (plugin entry point)
        build-schedule/SKILL.md              ← Builders
        build-report/SKILL.md
        create-scenario/SKILL.md
        variance-analysis/SKILL.md           ← Analysis
        margin-analysis/SKILL.md
        sku-rationalization/SKILL.md
        cohort-analysis/SKILL.md
        investor-readiness-analysis/SKILL.md
        product-cost-analysis/SKILL.md
        marketing-efficiency-analysis/SKILL.md
        inventory-analysis/SKILL.md
        trade-spend-analysis/SKILL.md
        monthly-report/SKILL.md              ← Monthly Report
        price-change-analysis/SKILL.md
        summarize-model/SKILL.md             ← Model Ops
        interrogate-model/SKILL.md
        audit-model/SKILL.md
        clean-model/SKILL.md
        optimize-model/SKILL.md
        qa-financials/SKILL.md               ← Finance QA
        compare-scenarios/SKILL.md           ← Scenarios
    mcp-server/                              ← Drivepoint MCP plugin
      .claude-plugin/plugin.json
      .mcp.json                              ← MCP server declaration (endpoint placeholder)
      skills/                                ← MCP-specific skills (none yet)
      README.md                              ← setup + endpoint configuration
  trial/
    welcome.md                               ← guided trial experience for prospects
  README.md
```

Each plugin lives in its own `plugins/<name>/` directory with its own
`.claude-plugin/plugin.json`, and is registered in `marketplace.json` via a
relative `source`. Relative sources resolve from the marketplace root.

## The `smartmodel` Plugin

Teaches any Claude session the SmartModel Protocol v6.0 grammar — the
AI-readable standard for Drivepoint Excel financial models:

- Navigate any SmartModel workbook by reading sheet structure, tab colors, and row grammar
- Identify input cells (Key Driver) vs. calculated results (Key Result) via column A storage markers
- Read and interpret machine-readable identifiers in column B
- Understand the date spine, period types, metadata block, settings block, and data sections
- Consult the imports system to know what external data the model needs

Install the `smartmodel` plugin once. When working with a SmartModel workbook,
the `smartmodel-protocol` skill is the canonical protocol entry point — invoke
it explicitly with `/skill smartmodel-protocol` when needed. Each skill is a
`<name>/SKILL.md` directory following the Claude plugin spec. The logical
groupings (Builders, Analysis, Model Ops, Scenarios) are documented in the tree
above, but the actual `skills/` directory is flat.

The canonical SmartModel Protocol v6.0 specification lives at
`plugins/smartmodel/skills/smartmodel-protocol/SKILL.md` — this is both the
protocol spec and the plugin entry point.

## The `mcp-server` Plugin

Packages the Drivepoint MCP server so a Claude session can connect directly to a
brand's Drivepoint analytics data (read-only). See
`plugins/mcp-server/README.md` for the tool surface and endpoint configuration.

> **Note:** the endpoint in `plugins/mcp-server/.mcp.json` is currently a
> placeholder (`https://YOUR-DRIVEPOINT-MCP-ENDPOINT`). Set it to the real
> Drivepoint MCP URL before the plugin will connect.

## Try Drivepoint (Trial Experience)

Share one of these links with prospects to launch a guided Drivepoint trial inside Claude:

**Claude Desktop / mobile (deep link):**
```
claude://claude.ai/new?q=Read%20https%3A%2F%2Fgithub.com%2FBainbridge-Growth%2Fdrivepoint-plugins%2Fblob%2Fmain%2Ftrial%2Fwelcome.md%20and%20follow%20the%20instructions%20inside%20it%20exactly
```

**Browser (claude.ai):**
```
https://claude.ai/new?q=Read%20https%3A%2F%2Fgithub.com%2FBainbridge-Growth%2Fdrivepoint-plugins%2Fblob%2Fmain%2Ftrial%2Fwelcome.md%20and%20follow%20the%20instructions%20inside%20it%20exactly
```

The link opens a new Claude conversation pre-filled with a prompt that loads `trial/welcome.md`. Claude reads the file, then runs a guided trial experience using a sample CPG brand (Oatwave). The prospect picks from five analysis paths (variance, cohort/margins, inventory/demand planning, investor readiness, SKU rationalization) and sees Drivepoint-quality output on sample data, with a CTA to connect their real data.

No install required. Works in any Claude surface: browser, Desktop app, or mobile. The `trial/` folder stays at the repo root so these links never change.

**To update the trial experience**, edit `trial/welcome.md` and push to main. The link never changes.

## Related Repos
| Repo | Purpose |
|------|---------|
| [drivepoint-smartmodel-templates](https://github.com/Bainbridge-Growth/drivepoint-smartmodel-templates) | Template content library (skills, imports, xlsx artifacts) |
| [drivepoint-smartmodel-utils](https://github.com/Bainbridge-Growth/drivepoint-smartmodel-utils) | Python tools for conversion, generation, validation |
