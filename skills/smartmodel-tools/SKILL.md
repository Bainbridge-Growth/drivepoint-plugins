---
name: smartmodel-tools
description: SmartModel utility tools for generating, validating, upgrading, and converting SmartModel workbooks
user-invocable: true
allowed-tools: Read, Grep, Glob, WebFetch
---

# SmartModel Tools

Utility tools for working with Drivepoint SmartModel workbooks. These tools call the Raptor service SmartModel API (`/api/v1/smartmodel/*`) to generate, validate, upgrade, convert, and list SmartModel templates.

---

## Authentication

All tool requests require a **bearer token** in the `Authorization` header. The token is resolved automatically from the plugin's authenticated session — it is **not user-visible** and should never be prompted for.

```
Authorization: Bearer <scoped_smartmodel_token>
```

The scoped token is only valid for `/api/v1/smartmodel/*` routes on the Raptor service.

---

## group_id Resolution

Every tool that operates on a specific tenant requires a `group_id`. This is resolved automatically from the authenticated user's company profile via the `sharepoint_site_id` field — the caller does not need to supply it explicitly.

<!-- TODO: group_id resolution approach needs to be confirmed with the team.
     Current implementation: resolved from authenticated user's tenant record
     using the sharepoint_site_id field. This may change to support explicit
     group_id passthrough or a different tenant lookup mechanism. -->

---

## Tools

### 1. `generate_smartmodel`

Create a new SmartModel workbook from a template configuration.

**Purpose**: Generates a fully structured SmartModel xlsx file from a named template, pre-populated with the correct sheet grammar, metadata blocks, settings, dimension/measure registries, and data sections per the v6.0 protocol.

**Endpoint**: `POST /api/v1/smartmodel/generate`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | string | yes | Template identifier (e.g., `dtc-revenue`, `opex`, `13wk-cashflow`) |
| `company_name` | string | yes | Company name to embed in Settings tab |
| `company_id` | string | yes | Drivepoint company ID |
| `start_date` | string | yes | Model start date in `YYYY-MM-DD` format |
| `historical_start_date` | string | no | Historical data start date. Defaults to 12 months before `start_date` |
| `currency` | string | no | Currency code. Defaults to `USD` |
| `dimensions` | array | no | Override default dimensions. Each item: `{ "slug": "...", "name": "..." }` |

**Request example**:
```json
{
  "template_id": "dtc-revenue",
  "company_name": "Acme Corp",
  "company_id": "acme-001",
  "start_date": "2026-01-01",
  "currency": "USD"
}
```

**Response**: Returns the generated SmartModel workbook as a binary xlsx download, or a JSON envelope with a signed URL for retrieval.

```json
{
  "status": "ok",
  "file_url": "https://storage.example.com/smartmodel/generated/acme-001_dtc-revenue.xlsx?sig=...",
  "template_id": "dtc-revenue",
  "protocol_version": "6.0"
}
```

---

### 2. `validate_smartmodel`

Run v6 protocol compliance checks on an existing SmartModel workbook.

**Purpose**: Validates that a workbook conforms to SmartModel Protocol v6.0 — checking Settings tab structure, metadata blocks, identifier naming conventions, column A markers, date spine, and sheet grammar rules.

**Endpoint**: `POST /api/v1/smartmodel/validate`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_url` | string | yes* | URL to the xlsx file to validate |
| `file_content` | string | yes* | Base64-encoded xlsx file content |
| `strict` | boolean | no | If `true`, treat warnings as errors. Defaults to `false` |

*One of `file_url` or `file_content` is required.

**Request example**:
```json
{
  "file_url": "https://storage.example.com/models/acme-model.xlsx",
  "strict": true
}
```

**Response**:
```json
{
  "status": "valid",
  "protocol_version": "6.0",
  "errors": [],
  "warnings": [
    {
      "sheet": "DTC",
      "row": 9,
      "rule": "metadata_name_must_be_string",
      "message": "D9 contains a formula; expected a plain string value"
    }
  ],
  "summary": {
    "sheets_checked": 5,
    "templates_found": ["dtc-revenue", "opex"],
    "settings_valid": true
  }
}
```

---

### 3. `upgrade_smartmodel`

Upgrade a SmartModel workbook from v5 to v6 protocol.

**Purpose**: Transforms a v5 SmartModel workbook to comply with v6.0 protocol grammar — migrating identifier formats, adding the Index tab manifest, updating Settings tab fields, and restructuring sheet grammar to match the v6 specification.

**Endpoint**: `POST /api/v1/smartmodel/upgrade`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_url` | string | yes* | URL to the v5 xlsx file to upgrade |
| `file_content` | string | yes* | Base64-encoded v5 xlsx file content |
| `dry_run` | boolean | no | If `true`, return a diff of changes without producing the file. Defaults to `false` |

*One of `file_url` or `file_content` is required.

**Request example**:
```json
{
  "file_url": "https://storage.example.com/models/legacy-model-v5.xlsx",
  "dry_run": false
}
```

**Response**:
```json
{
  "status": "ok",
  "file_url": "https://storage.example.com/smartmodel/upgraded/legacy-model-v6.xlsx?sig=...",
  "source_version": "5.0",
  "target_version": "6.0",
  "changes": [
    "Added Index tab with template manifest",
    "Migrated 3 sheets to v6 identifier format",
    "Updated Settings tab with required v6 fields"
  ]
}
```

---

### 4. `convert_to_smartmodel`

Convert a plain Excel workbook (.xlsx) into SmartModel format.

**Purpose**: Takes a standard Excel file containing financial data and restructures it into a v6.0-compliant SmartModel — inferring dimensions, measures, and time axes from the source data, and mapping them into the SmartModel sheet grammar.

**Endpoint**: `POST /api/v1/smartmodel/convert`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_url` | string | yes* | URL to the source xlsx file |
| `file_content` | string | yes* | Base64-encoded source xlsx file content |
| `template_id` | string | no | Target template to map data into. If omitted, the service infers the best fit |
| `company_name` | string | yes | Company name for the generated SmartModel |
| `company_id` | string | yes | Drivepoint company ID |
| `sheet_mapping` | object | no | Explicit mapping of source sheets to SmartModel sheet types |

*One of `file_url` or `file_content` is required.

**Request example**:
```json
{
  "file_url": "https://storage.example.com/uploads/raw-financials.xlsx",
  "company_name": "Acme Corp",
  "company_id": "acme-001",
  "template_id": "dtc-revenue"
}
```

**Response**:
```json
{
  "status": "ok",
  "file_url": "https://storage.example.com/smartmodel/converted/acme-001-converted.xlsx?sig=...",
  "inferred_template": "dtc-revenue",
  "protocol_version": "6.0",
  "mapping_summary": {
    "sheets_mapped": 3,
    "dimensions_detected": 5,
    "measures_detected": 12
  }
}
```

---

### 5. `list_smartmodel_templates`

Return the available template catalog.

**Purpose**: Lists all SmartModel templates available for generation, along with their metadata — template ID, display name, description, version, supported grain, and default dimensions.

**Endpoint**: `GET /api/v1/smartmodel/templates`

**Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `category` | string | no | Filter by template category (e.g., `revenue`, `opex`, `cashflow`) |
| `grain` | string | no | Filter by time grain (`monthly`, `weekly`, `quarterly`) |

**Request example**:
```
GET /api/v1/smartmodel/templates?category=revenue
```

**Response**:
```json
{
  "templates": [
    {
      "template_id": "dtc-revenue",
      "name": "DTC Revenue",
      "description": "Direct-to-consumer revenue forecast with SKU-level dimensions",
      "version": "1.0.0",
      "grain": "monthly",
      "category": "revenue",
      "default_dimensions": [
        { "slug": "sku-1", "name": "SKU 1" },
        { "slug": "sku-2", "name": "SKU 2" }
      ]
    },
    {
      "template_id": "amzn-revenue",
      "name": "Amazon Revenue",
      "description": "Amazon marketplace revenue with SKU-level dimensions",
      "version": "1.0.0",
      "grain": "monthly",
      "category": "revenue",
      "default_dimensions": [
        { "slug": "asin-1", "name": "ASIN 1" }
      ]
    }
  ]
}
```

---

## Error Handling

All tools return errors in a consistent format:

```json
{
  "status": "error",
  "error_code": "VALIDATION_FAILED",
  "message": "Human-readable error description",
  "details": {}
}
```

Common error codes:
- `AUTH_FAILED` — invalid or expired bearer token
- `VALIDATION_FAILED` — request parameters failed validation
- `TEMPLATE_NOT_FOUND` — requested template_id does not exist
- `PROTOCOL_MISMATCH` — file is not a recognized SmartModel version
- `CONVERSION_FAILED` — source file could not be mapped to SmartModel format
