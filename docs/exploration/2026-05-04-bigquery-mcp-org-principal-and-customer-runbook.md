# [Linear subticket] BigQuery MCP — official server, contract, tenant IAM, customer runbook

**Parent:** Link to Drivepoint MCP parent issue in Linear (set when creating).

**Type:** Exploration / architecture (no implementation in this note).

---

## Goal

Evaluate shipping the **official Google Cloud BigQuery MCP** (`https://bigquery.googleapis.com/mcp`) as a connector from the **external** `drivepoint-plugins` Claude plugin, with Drivepoint as query principal and customer-controlled allowlisting.

---

## A) Official Google BigQuery MCP — contract (tool surface)

Remote endpoint: `https://bigquery.googleapis.com/mcp` (Google-managed).

**Tools (from Google MCP reference):**

| Tool | Purpose |
|------|---------|
| `list_dataset_ids` | List datasets in a project |
| `get_dataset_info` | Dataset metadata |
| `list_table_ids` | Tables in a dataset |
| `get_table_info` | Table metadata |
| `execute_sql_readonly` | **SELECT-only** |
| `execute_sql` | **Full SQL** (DML/DDL/ML, etc.) |

**Product implications**

- Google steers agents toward **readonly** when possible; **`execute_sql`** remains a governance surface (IAM + product policy).
- Jobs labeled `goog-mcp-server: true`; billing tied to **`project_id`** on calls.
- **Plugin work** is mostly: MCP wiring in plugin manifest, **auth** to Google’s required flow, **docs**, and **Claude host** compatibility (remote MCP vs stdio).

**Reference:** [MCP Reference: bigquery.googleapis.com](https://docs.cloud.google.com/bigquery/docs/reference/mcp)

---

## B) “Contract” as product design (verbatim vs narrowed)

1. **Verbatim** — expose all six tools; enforce via **IAM** + customer process.
2. **Narrowed / wrapped** — fewer tools or stricter semantics (allowlists, max rows, no `execute_sql`); more maintenance.

**Choice for Drivepoint (initial):** Verbatim + **tight IAM on marts** + optional later wrapper if external customers need harder guarantees.

---

## C) Tenant model (agreed context)

- **One independent GCP project per customer** → maps cleanly to BigQuery **`project_id`** per tenant.
- **Governed mart tables** → IAM at **dataset** (or table) scope on marts only; historically **Google Groups** used for BQ rights in customer orgs.
- **Existing Drivepoint GCP OAuth client** → reuse depends on **which principal** runs queries and what Google’s **MCP auth** flow expects (may differ from web-app OAuth).

---

## D) Principal model — “we are the principal”

**BigQuery sees:** a **Drivepoint service account** (or equivalent) running jobs in the **customer project**.

**Customer allowlist Google Group (their side):**

- Best used as **Drivepoint product authorization** (“who may use Drivepoint for this tenant”), verified at login/session — **not** the same as putting humans on BigQuery IAM for SA-executed queries.
- **BigQuery IAM:** customer grants **Drivepoint SA** `BigQuery Data Viewer` (marts datasets) + **`BigQuery Job User`** at project level as required for jobs.

**Clarification for docs:** Do not conflate “users in allowlist group” with “BQ restricts SA” unless moving to **end-user credentials** or a different architecture.

---

## E) Customer-facing setup runbook (draft for docs)

### Drivepoint provides

- Drivepoint **service account email** for the tenant.
- Customer **GCP project ID** (linked tenant).
- **Mart dataset IDs** (or qualified allowlist).

### Step 1 — BigQuery IAM (customer admin, customer project)

1. BigQuery → each **mart dataset** → Sharing.
2. Grant **Drivepoint SA** → `BigQuery Data Viewer` on those datasets only.
3. Project IAM → grant same SA **`BigQuery Job User`** if required for query execution (validate minimal posture).

Avoid `BigQuery Admin` / broad `Data Editor` unless justified.

### Step 2 — Allowlist (customer admin / IT)

1. Create group, e.g. `drivepoint-users@customerdomain.com`.
2. Add end users allowed to use Drivepoint.
3. Share group email with Drivepoint; complete **admin consent / directory** steps Drivepoint requires for membership checks.

### Step 3 — Verify

- IAM: SA on datasets + job role.
- Drivepoint: smoke `SELECT 1` on allowed mart.
- Non-allowlisted user → denied at **app** layer.

### Step 4 — Ongoing

- Joiners/leavers → update **group**.
- New marts → repeat **dataset IAM** for Drivepoint SA.

### “IAM on our side”

Drivepoint cannot grant **inside customer project** without customer action (manual grants first; optional later: bootstrap automation with explicit customer consent).

---

## F) Claude org / Desktop / Excel notes (context)

- **Org GitHub marketplaces:** Cowork docs emphasize **Desktop**; org-synced repos are **private or internal** (not public).
- **`drivepoint-plugins` marketplace.json:** use **relative** `./` plugin source so `smartmodel` resolves inside the cloned repo (avoids anonymous second fetch failing for private org catalog).
- **Claude for Excel:** docs say **Skills** from Claude settings appear in Excel; **org Cowork plugins** are not clearly documented as identical for Excel — treat Skills path vs plugin path separately until confirmed with Anthropic.

---

## G) Open decisions (for implementation ticket)

1. Confirm **remote BigQuery MCP** + **Claude plugin MCP** auth wiring per current Anthropic + Google docs.
2. Per-tenant SA: one global vs one per customer project (naming, keyless WIF vs keys).
3. Whether to **document-disable** `execute_sql` at product policy vs rely on IAM only.
4. Customer doc portal placement + screenshots for Console IAM.

---

## Acceptance for this exploration ticket

- [ ] Product/engineering agrees on **SA + allowlist group (app)** split.
- [ ] Customer runbook reviewed by someone who has done **cross-tenant BQ IAM** before.
- [ ] Parent MCP epic linked; child implementation tickets spawned (auth, plugin manifest, docs).
