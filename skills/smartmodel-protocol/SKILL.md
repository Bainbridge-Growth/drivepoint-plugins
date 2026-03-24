---
name: smartmodel-protocol
description: Loads the SmartModel Protocol v6.0 grammar. Use when working with any Drivepoint SmartModel Excel workbook — reading structure, populating data, navigating sheets, rolling forward, or answering questions about financial model content.
user-invocable: false
allowed-tools: Read, Grep, Glob
---

# SmartModel Protocol Skill — v6.0
**Issuer**: Drivepoint (drivepoint.io)
**Hosted at**: `https://raw.githubusercontent.com/Bainbridge-Growth/drivepoint-smartmodel-protocol/main/protocol/v6.0/smartmodel-skill.md`
**Loaded by**: Drivepoint Excel add-in on workbook open
**Purpose**: Teach any AI agent the SmartModel grammar so it can read, navigate, assist with, and populate Drivepoint SmartModel workbooks

---

## What is a SmartModel?

A SmartModel is an Excel (.xlsx) workbook that follows a strict structural grammar — identifiers in column B, storage markers in column A, a date spine in row 2, and a Settings tab with model metadata. When the Drivepoint add-in opens a SmartModel (detected via `settings.smartmodelSpec = "6.0"` in the Settings tab), it reads each sheet's `metadata___template_id`, fetches the corresponding skills and import declarations from the Drivepoint API, and provides them to the AI agent as context.

The agent's job is to help users understand their model, populate it with data, roll it forward in time, diagnose errors, and answer questions about the business metrics it represents.

---

## File Structure

A SmartModel xlsx is a standard Excel zip archive. The file's job is to be a well-structured workbook — skills and import declarations live on the server, fetched at runtime by the authenticated add-in.

**What's in the file:**

| Component | Purpose |
|-----------|---------|
| Settings tab | Model identity, protocol version, configuration |
| Index tab | Template registry — lists all templates and their sheets |
| Schedule sheets (yellow) | Primary financial modeling sheets |
| Report sheets (blue) | Derived output reports |
| R- sheets (default) | Data import layer — one per import declaration |
| WebExtension | Embedded add-in reference (prompts install from AppSource) |

**What's on the server** (fetched by the add-in via Drivepoint API):

| Component | Purpose |
|-----------|---------|
| Protocol skill | Universal SmartModel grammar (this document) |
| Template skills | Template-specific instructions (one per template) |
| Import declarations | Data source definitions for each template's R- sheets |
| AI context | Additional context the agent needs for the specific model |

The WebExtension is the only custom content injected into the xlsx zip structure beyond standard Excel files. It references the Drivepoint add-in on Microsoft AppSource, enabling automatic add-in discovery when the workbook is opened.

---

## Sheet Types and Tab Colors

Every SmartModel workbook uses a consistent tab color system:

| Tab Color   | Sheet Type  | Purpose |
|-------------|-------------|---------|
| White       | Index       | Table of contents — first tab users see |
| Yellow      | Schedule    | Primary financial schedule sheets (forecasting, planning) |
| Blue        | Report      | Output reports and summaries |
| Default     | R- sheets   | Data import layer — one per import declaration |
| Dark gray   | Settings    | Machine-readable configuration, add-in owned |

**Index tab**: Human-readable table of contents. Shows registered templates, sheet ownership, data sources, and import status. Maintained by the add-in.

**Schedule tabs**: Where the primary financial modeling happens. Formula-driven. Reference R- sheets for live data. These are the sheets users interact with most.

**Report tabs**: Derived outputs. Reference schedule sheets. Read-only for most users.

**R- sheets** (prefix "R-"): Data import layer. One R- sheet per import declaration. Populated by the add-in from connected data sources, or manually by the user. Template formula sheets reference R- sheets dynamically via Excel formulas. The agent does not need to declare wiring between templates — connections are discerned at runtime by reading the formula layer.

**Settings tab**: Machine-readable key-value configuration. Column A is reserved/empty; columns B–E contain `id`, `setting`, `value`, `description`. Add-in owned, never user-edited directly.

---

## Settings Tab Structure

The Settings tab stores model configuration as a key-value table. The agent reads this tab to understand the model's identity and operational parameters.

**Column layout**: Column A is reserved (narrow, empty). Data starts at column B:
- Column B: `id` — dot-notation identifier (monospace font), e.g. `settings.smartmodelSpec`
- Column C: `setting` — human-readable label
- Column D: `value` — the stored value
- Column E: `description` — explanatory note

Required settings fields:

| ID | Setting | Value |
|----|---------|-------|
| `settings.smartmodelSpec` | Protocol Version | `6.0` |
| `settings.modelVersion` | Model Version | semver (e.g., `1.0.0`) |
| `settings.modelName` | Model Name | Human-readable string |
| `settings.modelType` | Model Type | `"template"` or `"model"` |
| `settings.modelStartDate` | ProForma Start Date | Date |
| `settings.historicalStartDate` | Historical Start Date | Date |
| `settings.companyId` | Company ID | Drivepoint company ID |
| `settings.companyName` | Company Name | Company name string |
| `settings.currency` | Currency | Default `USD` |
| `settings.author` | Author | Author name |
| `settings.authorId` | Author ID | Author identifier |

Settings IDs use dot notation (`settings.fieldName`). These are distinct from the identifier system used inside schedule sheets, which uses triple-underscore notation (described below).

`settings.smartmodelSpec = "6.0"` is the detection gate — the add-in checks this value to determine whether the workbook follows v6 protocol conventions.

---

## Sheet Grammar — How to Read a Schedule Sheet

Schedule sheets follow a strict row-by-row structure. Once you understand this grammar, you can navigate any SmartModel schedule sheet.

### The Header Block (Rows 1–8)

These rows are structural chrome that frames the sheet.

**Row 1 — Title bar**: Light blue background (`#64B1FF`), white text. Column A contains `≡` (section marker). Column C contains `=D9` (formula that displays the template name). Every cell has light blue background and white text — no exceptions.

**Row 2 — Date spine**: Black background, white bold text. Column C is labeled "End of Period". Starting at column K, each cell contains a month-end date formatted as `mmm-yy` (e.g., "Jan-24"). Dates extend right for the full time horizon (typically 48 months). This is the authoritative time axis for the entire sheet.

**Row 3 — Period type**: Gray background (`#808080`), white text. Column C is labeled "Period Type". Starting at column K, each cell contains either "Actual" or "Forecast" — right-aligned to visually correspond with the dates above. This tells you which columns contain historical data vs. forward projections.

**Row 4 — Status bar**: Very light gray background. Column A contains a blue bullet `•`. Column C contains a status message (e.g., "No Errors"). This row is maintained by the add-in.

**Rows 5–6**: Blank spacing.

**Row 7 — Template title**: Contains `=D9` in column C (bold, 14pt, black). A thick blue border (`#63AEFF`) runs along the bottom from column B to the last data column. This is a visual section divider.

**Row 8 — Template description**: Gray italic text in column C. Brief description of the template's purpose.

### The Metadata Block (Rows 9–15 typical)

Row 9 is critical. It anchors the entire template identity system:

- `B9` = `"metadata___name"` (monospace font — always)
- `C9` = `"Name"`
- `D9` = The actual template name string (e.g., `"13-Week Cash Flow"`) — **this must be a string value, not a formula**

Rows 10–15 contain additional metadata fields following the same pattern:
- Column B: identifier in monospace font, using `metadata___` prefix with triple underscores
- Column C: human-readable label in standard font
- Column D: value in standard font

Standard metadata fields:

| Row | Identifier | Example Value |
|-----|-----------|---------------|
| 9 | `metadata___name` | `"13-Week Cash Flow"` |
| 10 | `metadata___template_id` | `"13wk-cashflow"` |
| 11 | `metadata___template_version` | `"1.0.0"` |
| 12 | `metadata___description` | `"Weekly cash forecast..."` |
| 13 | `metadata___grain` | `"weekly"` |

`metadata___template_id` and `metadata___template_version` are how the add-in discovers which templates are present in the workbook. The add-in scans all sheets for `metadata___template_id` values, collects the unique IDs, and fetches the corresponding skills and import declarations from the server.

Other common metadata fields: `metadata___type`, `metadata___created`, `metadata___framework`.

**Column B rule**: Every cell in column B across the entire sheet uses monospace font (Menlo, size 10, black). This applies universally — metadata identifiers, settings identifiers, dimension identifiers, measure identifiers, data row identifiers. This is how you identify the machine-readable layer.

### The Settings Block (Rows 17–21 typical)

Sheet-level settings that control template behavior. Same three-column pattern as metadata:
- Column B: `settings___` prefix, triple underscores, monospace font
- Column C: human-readable label
- Column D: value (dates formatted `yyyy-mm-dd`)

Settings IDs are **always plural**: `settings___fy1_end_date`, not `setting___fy1_end_date`. This is non-negotiable.

A special setting `settings___identifier_structure` documents the pattern used to construct row identifiers in the data section (e.g., `pattern: "{dimension-slug}_{measure-code}"`).

### Dimension and Measure Registries

Before the data section, the sheet declares its dimensions and measures. These serve as the catalog of what the template models.

**Dimension registry**: Lists the dimensional entities (e.g., SKUs, channels, regions). Each row has:
- Column B: `dim_` prefix identifier (e.g., `dim_sku_1`) in monospace
- Column C: human-readable name (e.g., "SKU: Hydrating Face Serum")

**Measure registry**: Lists all metrics tracked. Each row has:
- Column B: `measure_` prefix identifier (e.g., `measure_orders`) in monospace
- Column C: human-readable name (e.g., "Orders")

Each registry section begins with a section header row (bold, 14pt, thick blue bottom border) and a subheader row (gray italic description), then a blank row, then data rows.

### Data Sections

The substantive modeling content. Each data section covers a category of metrics (e.g., "Orders & Revenue", "COGS", "Operating Expenses").

**Section header pattern** (3 rows):
1. Header row: bold 14pt black text in column C, thick blue border (`#63AEFF`) bottom from B to last column
2. Subheader row: gray italic description in column C
3. Blank spacing row

**Data rows**: Each row in a data section tracks one dimension × measure combination across the time horizon.

---

## Data Row Anatomy

This is the most important grammar element to understand. Every data row has four zones:

```
Col A  │  Col B                          │  Col C               │  Col K → last
───────┼─────────────────────────────────┼──────────────────────┼─────────────────
marker │  identifier formula             │  human label         │  time-series data
```

**Column A — Storage marker**: Determines whether this row is stored to the database and how users interact with it. Three possible values:

- `•` (bullet, blue `#4472C4`): Visual only. Not stored. Used for supporting inputs or reference values.
- `•⚡ Key Driver` (bullet + lightning + "Key Driver", black text): Stored to database as a **user input**. These are the cells the user edits to drive the model.
- `  ⚡ Key Result` (two spaces + lightning + "Key Result", black text): Stored to database as a **calculated result**. These cells contain Excel formulas — never hardcoded values.

**Column B — Identifier**: Contains a formula that generates the row's machine-readable identifier string. Example: `="hydrating-serum_orders"` — this displays the string `hydrating-serum_orders`. The identifier follows the pattern declared in `settings___identifier_structure`: `{dimension-slug}_{measure-code}`. Always monospace font.

**Column C — Label**: Human-readable description of what this row represents. Standard font.

**Columns K onward — Time series**: Actual or forecast values across the date spine defined in row 2.
- Actual columns (historical): contain reported values
- Forecast columns: **Key Driver** rows have editable cells (light gray background, blue-ish text) for user input; **Key Result** rows contain Excel formulas referencing their driver rows

### Total / Aggregation Rows

When meaningful (for additive measures like revenue, orders, spend — not for rates or percentages), a section closes with:
1. A blank separator row with a thin auto-color bottom border
2. A total row: `  ⚡ Key Result` marker, bold label in column C, SUM formulas in data columns

The separator border uses `'thin'` style, not `'thick'`.

---

## Input Cell Formatting

Forecast-period cells in Key Driver rows have distinct visual formatting to signal "this is editable":
- Light gray background
- Blue-ish text (theme color)

Actual-period cells and all Key Result cells remain white background, black text. This visual distinction is consistent across all SmartModel templates.

---

## Identifier Naming Conventions

The identifier system is how the add-in and agent address specific data points. The conventions are strict:

| Prefix | Usage | Example |
|--------|-------|---------|
| `metadata___` | Metadata fields (triple underscore) | `metadata___name` |
| `settings___` | Settings fields (triple underscore, always plural) | `settings___fy1_end_date` |
| `dim_` | Dimension registry entries | `dim_sku_1` |
| `measure_` | Measure registry entries | `measure_orders` |
| `{dim-slug}_{measure-code}` | Data row identifiers | `hydrating-serum_orders` |

**Triple underscore separator** (`___`): Used exclusively in metadata and settings identifiers. This is intentional — it visually and programmatically distinguishes structural metadata from data-layer identifiers.

**Dimension slugs**: Hyphenated lowercase. Derived from the dimension name (e.g., "Hydrating Face Serum" → `hydrating-serum`).

**Measure codes**: Camelcase or snake_case depending on the template's declared `settings___identifier_structure`.

---

## Formula Reference Rules

The agent must understand how formulas connect the sheet together:

- `C1` and `C7` always contain `=D9` — they display the template name
- `D9` always contains the template name as a **string value** (never a formula)
- Data row result cells reference input cells in the same column (e.g., `K51 = K49 * K50`)
- Formulas extend across all time-period columns
- R- sheet data is referenced by schedule sheets via standard Excel formulas — the agent reads these to understand data wiring between sheets

---

## Imports System

Import declarations define what external data each template needs. They are served by the Drivepoint API alongside template skills — not bundled in the xlsx file. The add-in fetches them when it discovers template IDs during workbook open.

Each import declaration maps to one R- sheet. The declaration specifies the data source, field schema, time dimension, and query parameters.

There are two fulfillment modes:
- **Without a Drivepoint account**: The add-in fills R- sheets from locally connected raw sources using best-effort matching, or the user populates manually
- **With a Drivepoint account**: The `dp_query` in each import declaration is executed directly against BigQuery with `{project_id}` and `{tenant_id}` injected at runtime

The agent receives import declarations as part of the skill context provided by the add-in. It should consult them to understand what data is available, which R- sheets are populated, and what the time dimension and field schema of each import is.

---

## Agent Operating Principles

When operating on a SmartModel, the agent should:

1. **Read Settings first**: Establish model identity (name, version, company, date range) before doing anything else
2. **Check import status**: Look at the Index tab and R- sheets to understand what data is populated vs. missing
3. **Navigate by marker type**: Use column A markers to distinguish inputs (Key Driver) from calculated outputs (Key Result)
4. **Never hardcode results**: Key Result cells must always use Excel formulas. If populating a Key Driver cell with data, write the value; if computing a Key Result, write the formula.
5. **Respect column B identifiers**: Use these to address specific data rows unambiguously, especially when the user asks about a specific metric
6. **Follow the time axis**: Row 2 is the authoritative date spine. Use it to locate the correct column for any given period
7. **Read the template skill**: This protocol skill teaches universal grammar. Template-specific skills are loaded by the add-in from the server and passed to the agent as context. They teach the semantics of each specific template — what each section means, how to roll it forward, common tasks, error handling
8. **Read the Index tab manifest**: The Index tab contains the template registry — a structured table listing every template ID, version, owned sheets, skill file, and imports file. This is the agent's map of the workbook. Read it before navigating schedule sheets.
9. **Be multi-template aware**: A working model typically contains 5–8 templates stitched together. The agent receives all relevant template skills and a sheet map showing which sheet belongs to which template.
10. **Do not infer connections between templates**: Formula wiring between sheets is discovered by reading Excel formulas at runtime, not declared in any configuration file

---

## Multi-Template Workbooks

A working SmartModel is typically 5–8 templates stitched together in a single workbook. Multi-template workbooks are first-class — each schedule sheet declares its template via `metadata___template_id` in its metadata block, and the Index tab provides a manifest of all templates for fast discovery.

**How it works:**

1. Workbook opens → add-in reads Settings tab → `settings.smartmodelSpec = "6.0"` confirms v6
2. Add-in reads the Index tab template manifest (single table read — no sheet scanning)
3. Extracts template IDs, versions, and skill/import file references
4. Fetches skills and import declarations for all templates in one API call
5. Caches skills in memory, passes them to the AI agent on chat open

Cross-template connections are standard Excel formulas — one schedule sheet referencing cells in another. The agent discovers these at runtime by reading the formula layer, not from any configuration file.

---

## Index Tab as Template Registry

The Index tab contains a structured template manifest — a machine-readable table that lists every template in the workbook. This is the **primary discovery mechanism** for both the add-in and the AI agent.

### Manifest Table Structure

The manifest is a table in the Index tab with the following columns:

| Column | Header | Content |
|--------|--------|---------|
| A | Template ID | Machine-readable identifier (e.g., `dtc-revenue`) |
| B | Version | Semver (e.g., `1.0.0`) |
| C | Sheets | Comma-separated list of owned sheet names |
| D | Skill File | Filename of the template skill (e.g., `dtc-revenue-skill.md`) |
| E | Imports File | Filename of the import declarations (e.g., `dtc-revenue-imports.yaml`) |

Example:

```
Template ID          Version  Sheets                                    Skill File                   Imports File
dtc-revenue          1.0.0    DTC, DTC - OTP, DTC - SUB, DTC - Acq     dtc-revenue-skill.md         dtc-revenue-imports.yaml
amzn-revenue         1.0.0    AMZN, AMZN - OTP, AMZN - SUB             amzn-revenue-skill.md        amzn-revenue-imports.yaml
wholesale-revenue    1.0.0    Wholesale                                 wholesale-revenue-skill.md   wholesale-revenue-imports.yaml
opex                 1.0.0    Opex                                      opex-skill.md                opex-imports.yaml
consolidation        1.0.0    M - Monthly                               consolidation-skill.md       consolidation-imports.yaml
```

### How it's used

- **Add-in**: Reads the manifest on workbook open. Extracts template IDs, versions, and file references. Sends one API request to fetch all skills and imports. No sheet scanning required.
- **AI agent**: Reads the manifest to understand what templates are present, which sheets belong to which template, and what skills are available. This is the agent's map of the workbook.
- **Maintenance**: The add-in updates the manifest when templates are added or removed. The manifest is the source of truth for what's in the workbook.

Each schedule sheet still declares `metadata___template_id` in its metadata block — this is the per-sheet identity that the agent uses when working on a specific sheet. The Index tab manifest is the workbook-level registry for discovery and fetching.

---

## Versioning

- **Protocol versioning**: Major.minor (e.g., `6.0`). Breaking grammar changes increment the major version.
- **Template versioning**: Semver (e.g., `1.0.0`). Template skill files and xlsx artifacts are versioned together.
- The protocol version is declared in `settings.smartmodelSpec` in the Settings tab.
- The template version is declared in `settings.modelVersion`.

---

## Quick Reference — Reading a Sheet Cold

When you open an unfamiliar SmartModel schedule sheet and need to orient quickly:

1. **Row 2** → What time periods does this model cover?
2. **Row 3** → Where does Actual end and Forecast begin?
3. **D9** → What is this template called?
4. **Metadata block** → What type, grain, and version is this template?
5. **Settings block** → What fiscal year dates and other parameters are configured?
6. **Dimension registry** → What entities are being modeled?
7. **Measure registry** → What metrics are tracked?
8. **Data sections** → What does column A say? If `•⚡ Key Driver`, it's user input. If `  ⚡ Key Result`, it's calculated.
9. **Column B** → What is the machine identifier for this specific row?
10. **R- sheets** → What real data is imported and feeding this model?
