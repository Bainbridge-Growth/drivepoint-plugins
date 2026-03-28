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

## SmartModel Tools

The `smartmodel-tools` skill exposes five utility tools for working with SmartModel workbooks via the Raptor service API:

| Tool | Description |
|------|-------------|
| `generate_smartmodel` | Create a new SmartModel workbook from a template configuration |
| `validate_smartmodel` | Run v6 protocol compliance checks on an existing workbook |
| `upgrade_smartmodel` | Upgrade a v5 workbook to v6 protocol format |
| `convert_to_smartmodel` | Convert a plain xlsx file into SmartModel format |
| `list_smartmodel_templates` | List available templates in the catalog |

Invoke with `/skill smartmodel-tools` or use tools directly in a Claude session.

### Authentication Setup

SmartModel tools authenticate against the Raptor service using a **scoped API key** that is only valid for `/api/v1/smartmodel/*` routes. Configure the token in the Raptor service settings:

```json
{
  "service": {
    "smartmodel_access_token": "<your-scoped-token>"
  }
}
```

The scoped token is separate from the primary `service.access_token` and cannot access other Raptor service routes. The primary access token continues to work for all routes, including SmartModel.

The bearer token is resolved from the plugin's authenticated session and is not visible to end users.

### group_id Resolution

The `group_id` required by SmartModel operations is resolved from the authenticated user's company profile via the `sharepoint_site_id` field. Callers do not need to supply it explicitly — it is injected by the plugin's server-side component based on the tenant context.

> **Note**: The `group_id` resolution approach is subject to change. See the TODO in `skills/smartmodel-tools/SKILL.md` for details.

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
    smartmodel-tools/
      SKILL.md           ← SmartModel utility tool definitions
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
