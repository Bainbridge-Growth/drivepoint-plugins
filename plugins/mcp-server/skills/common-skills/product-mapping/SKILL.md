# Product Mapping

How to decide when two product records — from the same channel over
time, or from different channels — refer to the same physical product,
and how to record those decisions with the MCP product-mapping tools.

Reading this skill is required any time the user asks to "map
products", "reconcile products", "crosswalk SKUs across channels",
"deduplicate the catalog", "clean up the catalog", "match Amazon to
Shopify products", or names the product-mapping flow. This is the
Drivepoint equivalent of the industry's _product crosswalk / entity
resolution / master-data-reconciliation_ workflow — the vocabulary
varies, the job is the same: one canonical product per physical unit,
every channel row tied back to it.

The MCP server exposes exactly three product-mapping tools:

- `read_product_mapping_source` — read-only; returns the cross-channel
  product roster (one row per `channel/stores/sku/title`) from the
  customer's BigQuery warehouse. Each record also carries an
  `existing` field: the last saved decision for that sourceKey (or
  `null` on first-run). The response's `existingMappingCount` tells
  you whether this is a re-run.
- `save_product_mappings_to_firebase` — **DELTA-MERGES** your changes
  into the company's Firestore mapping document. Firestore stores
  **decisions only** (`confirmed` + `rejected`); `unmapped` is
  expressed by absence. Takes three inputs: `mappings` (a CSV of NEW
  or CHANGED confirmations), optional `rejected_source_keys` (a JSON
  array of sourceKeys to bulk-reject), and optional
  `unmapped_source_keys` (a JSON array of sourceKeys to explicitly
  demote back to unmapped). **Rows you don't mention keep their prior
  state** — do NOT re-send unchanged confirmations.
- `publish_product_mappings_to_bigquery` — reads the confirmed
  decisions out of Firestore and **fully OVERWRITES** the mapped-
  products catalog table in BigQuery.

Everything else is out of scope. Do not use `run_query`, `list_tables`,
or any other data-catalog tool as part of a mapping — the source table
`product_mapping_source` is pre-unioned across channels by dbt, and
the tools above already query it.

---

## Three ideas to hold in your head (read this first)

Everything else in this skill is scaffolding around these three rules.
If you only remember three things, remember these:

1. **The canonical id is DERIVED, never invented.** Same physical
   product → same `drivepointMappedId` on every run and across every
   channel, because the id is a deterministic slug of `productFamily +
flavor/variant + sizeVariant`. You never look up "what id did I use
   last time?" — you re-derive it and it matches.
2. **The canonical VALUES are SELECTED from the source rows, never
   fabricated.** `drivepointMappedProductName`, `drivepointMappedSku`,
   and `productDescription` are chosen from the strings the customer
   already uses somewhere in their own data. Prefer **null** over a
   plausible-sounding guess. You are picking a representative, not
   writing marketing copy.
3. **The roster is your context, not a database.** One
   `read_product_mapping_source` call puts the entire cross-channel
   roster into your working memory. You do the mapping by reading it
   inline — grouping, comparing, and deciding in your head. **Do NOT
   spawn scripts to re-analyze the roster.** Concretely, do not run
   `code_execution` (or any shell/python tool) to "inspect the
   structure", "preview payloads", "summarize statuses/channels",
   "list canonicals", "dump unmapped rows", "check the stores
   dimension", "list previously rejected rows", "see confirmed
   sourceKeys per canonical", or "sample titles for disambiguation".
   Every one of those is inline reading of data you already have.
   Each script round-trip costs 10-30 seconds of pure overhead for
   information already in your context. The ONE code_execution call
   that earns its cost is the final RFC-4180 CSV writer at save time
   — everything else, read inline and decide inline.

If you catch yourself typing a title, SKU, or description that doesn't
appear (in any form) in the source roster, stop — you are inventing,
which corrupts the crosswalk.

If you catch yourself planning a multi-step "let me first explore the
data, then group by X, then dump the Y set" pipeline, stop — you are
building the decision engine the skill forbids one script at a time.
Cancel the pipeline, read the roster inline, commit to the decisions.

---

## Re-runs — the roster remembers

`read_product_mapping_source` returns each row with its last saved
decision attached as `existing` (or `null` on the very first run for
this customer). Treat `existingMappingCount > 0` as the signal you are
in a **re-run**, not a fresh mapping.

On a re-run:

- **The existing decisions are the baseline.** Trust them unless you
  have a reason to change one. Do not re-derive canonical ids or
  re-select names/SKUs for rows whose `existing.status = confirmed`
  and whose source fields haven't drifted meaningfully.
- **Save is a MERGE — send only what changed.** The `mappings` CSV
  should contain ONLY new confirmations, confirmations you're
  correcting, and rare rejections that need explicit fields.
  Unchanged confirmations are omitted entirely; they keep their prior
  state in Firestore automatically. Bulk rejects go through
  `rejected_source_keys`. Rows you want to undecide go through
  `unmapped_source_keys` (see "The save call").
- **Focus your judgment on three groups:** (a) rows with
  `existing = null` (brand new since last run), (b) rows with
  `existing.status = unmapped` (previously flagged, still open),
  (c) rows whose source title/SKU has drifted since the previous
  mapping (rare, but happens with rebrands and marketplace edits).

On a first-run (all `existing = null`) the workflow is the same as it
has always been — derive everything, decide everything, emit
everything. There's just no prior state to preserve yet.

---

## The one workflow

Follow these steps in order. Never skip a step, never reorder them.

1. **Read ONCE, then reason inline — no follow-up scripts.** Call
   `read_product_mapping_source` a single time for the entire roster.
   Do NOT split the read by channel, by key type, or by SKU presence.
   One read, one roster in context. Each record carries an `existing`
   field with the last saved decision — check `existingMappingCount`
   to see if this is a re-run. **Once the roster is loaded, do not
   run any script to inspect, preview, summarize, filter, dump, or
   sample it.** All subsequent analysis is inline reading. See "Three
   ideas to hold in your head" rule #3.
2. **Normalize titles and sizes in place.** As you read each row,
   mentally apply the normalization rules in the next section. Do not
   write a script for this — do it inline as you group. (On re-runs,
   most rows already have a canonical mapping — you're normalizing to
   spot drift, not to re-derive everything.)
3. **Block, then group.** Cluster rows first by an obvious grouping
   attribute (brand line / product family), then within each block
   group by normalized title + normalized size into candidate
   canonical products. Blocking keeps you from comparing every row to
   every other row and is how a human analyst actually does this.
   On re-runs, the `existing.drivepointMappedId` already gives you
   the groups for free — use it as your blocking key and only cluster
   the rows with `existing = null` or `existing.status = unmapped`.
4. **Assign each group a canonical id** using the derivation rule
   below. Never invent an arbitrary id. (On re-runs, keep the
   existing id unless the product has genuinely changed.)
5. **Select the canonical values** for each group — name, SKU,
   description, attributes — from the source rows themselves, using
   the rules in "Choosing the mapped values". Never fabricate. On
   re-runs, if the existing values still fit, you don't need to
   re-supply them — merge semantics keep the prior Firestore row as-is
   when you omit it from the CSV (see "The save call").
6. **Resolve leftover rows** using the join-key ladder in Part 2:
   exact internal SKU, then UPC, then name semantics. Flag anything
   resolved by name semantics alone as `unmapped` (omit the patch).
7. **Hold the per-sourceKey decision set in your head.** As you group,
   commit to one decision per source row — `confirmed` (with its
<<<<<<< HEAD
   canonical), `rejected`, or `unmapped` — so the mapping is *already
   done* before you build the artifact. For each canonical group, know
=======
   canonical), `rejected`, or `unmapped` — so the mapping is _already
   done_ before you build the artifact. For each canonical group, know
>>>>>>> staging
   which sourceKeys belong to it and what the shared attributes are;
   for each reject, know its sourceKey. **Do NOT write this table out
   as scratch text** — on a 500+ row roster that's thousands of extra
   output tokens for something you already know inline. Just keep it
   organized: canonical → list of member sourceKeys + shared
   attributes; reject list → sourceKeys. The artifact is a rollup, and
   the save is a straight serialization — both read from this in-head
   set, so it has to be complete before step 8.
8. **Present the canonical summary + flagged rows** as a JSX/React
   artifact (see "Presenting the result"). The artifact aggregates
   the step-7 set for human review — one row per canonical, not per
   source row — but the underlying decisions are still per sourceKey.
   On re-runs, call out what CHANGED since the last mapping (new
   rows, drift, corrections) — that's the useful review, not the
   unchanged baseline.
9. **STOP. Wait for explicit user approval.** See the "Approval gate"
   block below — this is a hard stop, not a soft one.
10. **Call `save_product_mappings_to_firebase` ONCE**, serializing
    your in-head decision set from step 7 into the CSV — one row per
    confirmed sourceKey, with the shared canonical attributes copied
    across each alias — plus the rejections into
    `rejected_source_keys`, plus any demotions in
    `unmapped_source_keys`. **Do not re-enumerate aliases from the
    roster here** — step 7 already committed which sourceKeys belong
    to which canonical. If you find yourself scanning the roster
    row-by-row at save time to figure out membership, you skipped
    step 7 — commit to the groupings first, then come back. **Merges
    into the Firestore doc.** On re-runs the payload is typically
    small — only the rows whose decisions changed.
11. **Call `publish_product_mappings_to_bigquery` ONCE.** **Overwrites
    the BigQuery catalog table.** If this call fails after save, rerun
    publish — the Firestore doc is already correct, do not re-save.

**Reason inline. Do not script the decision-making.** The mapping
judgment — normalization, grouping, canonical id derivation, value
selection, rejection calls — happens in your head against the roster
in your context. The tool response IS the roster; do not try to
re-materialize it as a file, do not build a "decision engine" script
that iterates over it, do not spend turns hand-transcribing 500+
source rows into records.json so a script can read them. Your script
environment cannot reference the tool response as a file — the only
place the roster exists is in your context, and inline reasoning is
the only workflow that respects that.

**Scripts are appropriate only for CSV serialization at the very
end**, once your complete decision set already exists inline. If you
write a script for that, use a real CSV library (Python's `csv`
module, Node's `csv-stringify`) — the naive `join(",")` silently
corrupts any row whose title contains a comma. The CSV you pass to
`save_product_mappings_to_firebase` must be **RFC 4180 compliant**:
quote any field containing a comma, double quote, or newline with
`"..."`, and escape embedded quotes as `""`. For most rosters,
emitting the CSV inline is also fine — just quote every field that
could contain a delimiter.

---

## Approval gate — DO NOT SKIP

Between step 8 (render the artifact) and step 10 (call save) there is
a **hard stop**. The user reviews the artifact and explicitly tells
you to proceed. You do not save until they do.

- After rendering the artifact, your next message ends with a short
  prompt: _"Review the map above. Reply `save` (or `looks good`,
  `proceed`, `publish`) to write to Firestore, or tell me what to
  change."_
- **Do NOT call `save_product_mappings_to_firebase` on the same turn
  as the artifact.** The artifact is for the user's eyes, not a
  self-triggering signal.
- **Do NOT call save on a follow-up turn unless the user's latest
  message is an explicit approval.** A neutral message ("ok",
  "thanks", "cool") is NOT an approval — ask again. A request for
  changes is not an approval — regenerate the artifact.
- **Do NOT infer approval from your own confidence.** "I've validated
  the counts and everything looks right" is not a reason to save;
  it is a reason to _ask_.
- **Do NOT save partially "to make progress".** If the user hasn't
  approved yet, there is nothing to save.

Bypassing this gate is the single most-reported failure of this
workflow. The user has been burned by silent saves; they treat any
save without prior approval as broken behavior. If you are ever
unsure whether the user has approved, the answer is no — ask.

---

## Normalization — do this inline as you read

Every comparison you make happens on the normalized form of a title
and size. Two spellings of the same product must reduce to the same
normalized form or they will land in two different canonicals.

### Title normalization

Apply, in this order:

1. Lowercase.
2. Strip punctuation (`, . ' " ( ) [ ] & / \ |` → space).
3. Collapse whitespace.
4. Strip subscription and pack suffixes that are marketing artifacts,
   not product distinctions: `subscribe & save`, `subscription`,
   `auto-delivery`, `- one-time`, `- otp`.
5. Expand common abbreviations to a single form: `ct` / `count` /
   `pk` / `pack` → `pack`; `lb` / `lbs` / `pound` → `lb`; `oz` /
   `ounce` / `ounces` → `oz`; `ml` / `milliliter` → `ml`.
6. Move the size to the end if it's mid-string, so all forms end
   `<name> <flavor> <size>`.

### Size normalization

Pick ONE canonical string per unique physical size and use it
everywhere. Preferred form: number + unit, no space, lowercase.
Preserve the customer's unit system — do not convert oz to grams.

| Source variants                             | Canonical |
| ------------------------------------------- | --------- |
| `32 oz`, `32oz`, `32 fl oz`, `32-FL-OZ`     | `32oz`    |
| `2 lb`, `2LB`, `2 pound`, `2-lb`            | `2lb`     |
| `500 ml`, `500ML`, `500-ml`                 | `500ml`   |
| `12 ct`, `12-Pack`, `12 pack`, `Case of 12` | `12pack`  |
| `Single`, `1-pack`, `each`                  | _omit_    |

Only include `1pack` / `single` in the canonical string when the same
product also exists as a multipack — otherwise it's noise.

### What NOT to normalize away

Discriminating attributes (flavor, size, pack count, formulation)
MUST survive normalization. `Vanilla 32oz` and `Chocolate 32oz` are
two canonical products, not one. `Vanilla 32oz` and `Vanilla 2lb` are
two canonical products, not one. Collapsing them silently is the
single most common mapping bug — always split real variants.

---

## Canonical id derivation — compute, never invent

`drivepointMappedId` = `slug(productFamily) + '-' + slug(flavor/variant) + '-' + slug(sizeVariant)`

- Lowercase.
- Non-alphanumerics collapsed to single hyphens.
- Trim leading/trailing hyphens.

Example: `Protein Powder` / `Vanilla` / `2lb` → `protein-powder-vanilla-2lb`.

When a component is unknown, omit that segment rather than
substituting a placeholder. Because the id is derived, the SAME
physical product produces the SAME id every run and across channels
— that shared id IS the crosswalk. You never need to remember
previously-assigned ids.

`drivepointMappedId` is an internal stable key. It is NOT a
customer-facing SKU — see `drivepointMappedSku` below for that.

---

## Choosing the mapped values — pick, don't invent

Once a canonical group is formed, decide its representative values.
Every field is selected from source data or left null.

### `drivepointMappedProductName`

The human-readable name of the canonical product. Pick, don't write.

- **Prefer** the DTC / Ecommerce channel's product title (the
  customer's own storefront copy), after title normalization.
- **Fall back** to the shortest clean title across the group's source
  rows.
- **Structure**, when the pieces are known: `Brand Product Flavor
Size` (e.g. `Acme Protein Powder Vanilla 2lb`). Do not add
  marketing adjectives ("premium", "delicious") that are not present
  in any source row.
- **Never** synthesize a title from parts if none of the source rows
  actually says it that way.

Every row sharing a `drivepointMappedId` MUST have the same
`drivepointMappedProductName`. Decide it once per canonical, then
repeat verbatim.

### `drivepointMappedSku`

The customer's canonical SKU for the product. **Reuse, never mint.**

- **Prefer** the customer's own internal item number if one appears
  in the roster — usually the DTC/Ecommerce SKU, occasionally an
  internal number that shows up on retail-partner feeds too. This is
  the "master SKU" in PIM terminology.
- **Fall back** to the DTC channel's SKU when no shared internal
  number exists.
- **Set to null** when the customer has no consistent SKU across the
  group. Null is _more useful_ than a fabricated string — a null
  tells the operator "we need to pick one," a fabrication silently
  becomes truth.
- Retailer item numbers, ASINs, opaque scan IDs, and UPCs are NOT
  candidates for `drivepointMappedSku` — those are external channel
  ids, tracked by the source row, not the customer's own SKU.
- **Never invent** a new SKU string (e.g. `PP-VAN-2LB`) that doesn't
  appear anywhere in the customer's data.

### `productDescription`

Short human-readable description. Pick from source or null.

- **Prefer** the DTC listing's short description if the roster
  carries one; otherwise a retailer shelf-label description.
- **Set to null** when no source row supplies one. Do not paraphrase,
  do not summarize a long description into a short one, do not write
  from scratch.

### Attribute fields (`productFamily`, `productCategory`, `productFormat`, `sizeVariant`)

These may be _derived_ by cleaning/standardizing source values, but
must be traceable to source signal. Examples:

- `productFamily`: `Protein Powder` derived from source titles like
  "Whey Protein Powder", "Protein Pwdr", "Protein Powder - Vanilla".
  ✓ traceable.
- `productCategory`: `Supplements` — acceptable if source rows or
  retailer categories consistently place this family in that
  category. Null when no signal.
- `productFormat`: `Powder` / `Ready-to-Drink` / `Capsule` — pick
  from a small controlled vocabulary. Null when unclear.
- `sizeVariant`: the canonical size string from the normalization
  table above (`32oz`, `2lb`, `12pack`).

**Every row sharing a `drivepointMappedId` MUST carry identical
values for name, family, category, format, and size.** These are
attributes of the canonical product, not of the source row — decide
them once per canonical, then repeat verbatim.

Prefer null over guessing on any target field: a confidently-null
attribute is more useful than a fabricated one.

---

## The save call

`save_product_mappings_to_firebase` is a **delta merge**. Firestore
stores only decisions (`confirmed` + `rejected`); `unmapped` is
expressed by absence. Rows you don't mention keep their prior state.

It takes three inputs:

- **`mappings`** — a CSV of NEW or CHANGED confirmations (and rare
  rejections that need explicit fields). Line 1 is the header; one
  data line per row you're adding or correcting. **Every confirmation
  MUST carry the full mapped-\* / product-\* fields.** There are no
  "shortcut" rows — a confirmation with empty fields is dropped and
  counted in `invalidConfirmedCount`. Omit this argument entirely
  (or pass a header-only CSV) if this save is only demotions and
  bulk rejects.
- **`rejected_source_keys`** _(optional)_ — a JSON array of sourceKey
  strings to mark `rejected` in bulk. Use for POS junk, promotional
  lines, donations, samples — anything you're rejecting with no
  mapped fields to record. Much cheaper than CSV rows. Do NOT also
  include these sourceKeys in the CSV.
- **`unmapped_source_keys`** _(optional)_ — a JSON array of sourceKey
  strings to **demote** back to `unmapped`. Use when un-confirming or
  un-rejecting a row you decided on previously. The server deletes
  that decision from Firestore, and the row shows `status = unmapped`
  on the next read. **Silent omission does NOT demote** — a row you
  simply don't mention keeps its prior state. To remove a prior
  decision, you must list the key here.

### Merge semantics

<<<<<<< HEAD
| Situation                                     | Emit                                                            |
| --------------------------------------------- | --------------------------------------------------------------- |
| New confirmation (previously unmapped / new)  | Full CSV row with all decided values                            |
=======
| Situation                                      | Emit                                                            |
| ---------------------------------------------- | --------------------------------------------------------------- |
| New confirmation (previously unmapped / new)   | Full CSV row with all decided values                            |
>>>>>>> staging
| Changed confirmation (correcting an attribute) | Full CSV row with the corrected values                          |
| Unchanged confirmation                         | **Nothing** — omit entirely; Firestore keeps the prior decision |
| Bulk reject                                    | Add the sourceKey to `rejected_source_keys`                     |
| CSV reject that needs explicit fields          | Full CSV row with `status = rejected`                           |
<<<<<<< HEAD
| Undo a prior confirmation or rejection        | Add the sourceKey to `unmapped_source_keys`                     |
=======
| Undo a prior confirmation or rejection         | Add the sourceKey to `unmapped_source_keys`                     |
>>>>>>> staging

**On re-runs, a typical save is a handful of rows** — the new
decisions since last time, plus any corrections. The vast majority
of previously-confirmed / previously-rejected rows are untouched and
stay as-is in Firestore.

### Columns (CSV)

Pick whichever subset you need; always include `sourceKey` and
`status`, and always fill in mapped-\* / product-\* fields on every
`confirmed` row:

- `sourceKey` — copy verbatim from the source row
  (`channel::stores::sku`, falling back to title). This is how the
  server rejoins your row to the source row. Required.
- `status` — `confirmed` or `rejected`. Required. (Demotions to
  `unmapped` go through `unmapped_source_keys`, not the CSV.)
- `drivepointMappedId` — derived per the rule above. Required on
  every `confirmed` row.
- `drivepointMappedProductName` — selected per "Choosing the mapped
  values". Required on every `confirmed` row.
- `drivepointMappedSku`, `productFamily`, `productCategory`,
  `productFormat`, `sizeVariant`, `productDescription` — per
  "Choosing the mapped values"; empty cell when unknown.

**An empty cell is null.** Two commas in a row (`,,`) marks "unknown
/ not applicable" for that column — but a `confirmed` row that has
ALL mapped-\* / product-\* cells empty is treated as invalid (see
`invalidConfirmedCount`) and dropped.

**Never include `channel`, `stores`, `sku`, `title`, or `productType`
columns.** The server rehydrates those from BigQuery via `sourceKey`;
including them in the CSV wastes tokens and is ignored.

**Quote fields per RFC 4180.** Wrap any field that contains a comma,
a double quote, or a newline in `"..."`, and escape embedded double
quotes as `""`. Most rows won't need quoting, but titles and
sourceKeys occasionally do — silent truncation on the first
comma-containing row is the single most common bug in this workflow,
so quote whenever a field could contain a delimiter. If you're
serializing the CSV via a script, use a real CSV library (Python
`csv`, Node `csv-stringify`) that handles this automatically.

### Example — a small re-run save

Two new confirmations, one attribute correction, a bulk reject list,
and one previously-confirmed row being undecided:

**`mappings` (CSV):**

```csv
sourceKey,status,drivepointMappedId,drivepointMappedProductName,drivepointMappedSku,productFamily,productCategory,productFormat,sizeVariant
Shopify::Mad Rabbit::2PK-B-VAN,confirmed,tattoo-balm-vanilla-coconut-2pack,Tattoo Balm,2PK-B-VAN,Tattoo Balm,Targeted Tattoo Aftercare,Balm,2pack
Shopify::Mad Rabbit::3PK-B-VAN,confirmed,tattoo-balm-vanilla-coconut-3pack,Tattoo Balm,3PK-B-VAN,Tattoo Balm,Targeted Tattoo Aftercare,Balm,3pack
Shopify::Mad Rabbit::BALM-CUC,confirmed,tattoo-balm-cucumber,Tattoo Balm,BALM-CUC-V2,Tattoo Balm,Targeted Tattoo Aftercare,Balm,
```

**`rejected_source_keys` (JSON array):**

```json
[
  "Shopify::Mad Rabbit::Charge for Premiere",
  "Shopify::Mad Rabbit::FLAT DONATION 5847",
  "Shopify::Mad Rabbit::tester-product"
]
```

**`unmapped_source_keys` (JSON array):**

```json
["Shopify::Mad Rabbit::LEGACY-SKU-42"]
```

Reading this row-by-row:

- `2PK-B-VAN` and `3PK-B-VAN` are fresh confirmations — full attributes.
- `BALM-CUC` corrects the master SKU from `BALM-CUC` to `BALM-CUC-V2` —
  full row so the correction is unambiguous.
- The three `rejected_source_keys` become `rejected` decisions
  server-side.
- `LEGACY-SKU-42` was previously confirmed (or rejected) — listing it
  in `unmapped_source_keys` deletes that decision.
- **Every other previously-confirmed row in the roster is untouched
  and stays confirmed** — that's the merge, and that's why the
  payload can stay small.

On a **first-run** the pattern is the same, just with more full rows
in the CSV — there is no prior state to preserve.

---

## Part 1 — Within a channel: consolidate drift

One real product shows up under many titles/SKUs over time (rebrands,
listing edits, punctuation drift, a subscription suffix appended
later). Collapse the drift onto one canonical product per channel.

- **Match key: SKU when present on both sides, title as the
  fallback.** Don't match on title alone when a stable SKU exists —
  title text drifts (marketing copy, subscription suffixes) in ways
  a SKU doesn't.
- **SKU reuse vs. rename.** If a SKU was genuinely reused for a
  DIFFERENT product at some point (not just a cosmetic rename),
  treat the two eras as different canonical products. Flag both as
  `unmapped` and call out the reuse — folding all history under one
  id silently corrupts historical reporting.
- **Alias SKUs.** Ecommerce often carries extra SKUs for the same
  product (subscription variants, legacy codes, wholesale-prefixed
  codes). Fold them onto the canonical the primary SKU defines by
  matching title + variant; don't treat them as separate products.
- **Bundles/kits.** A kit sold as one SKU represents several
  component products. Map it to a single canonical bundle product
  and set `status` to `unmapped`, describing the components in the
  review table so the customer can confirm how to split it. Never
  silently map a bundle as if it were one simple unit.
- **Drop $0 promotional/gift lines with `rejected`.**

---

## Part 2 — Across channels: crosswalk the same physical product

Once each channel has its canonical products, tie the same physical
product together across channels. Because ids are derived from
family + flavor + size, the same product resolves to the same id
automatically — your job is confirming that two rows really are the
same product.

What each channel gives you to match on:

- **Ecommerce / DTC** — primary key: internal SKU; also carries
  product title + variant (pack/size).
- **Retail sell-through (per-retailer feeds)** — primary key:
  retailer item number; also carries retailer SKU, UPC, partner
  name; the only human-readable field is usually the shelf-label
  description (a real "product name" column is frequently blank).
- **Distribution / grocery scan** — primary key: an opaque scan ID
  (no SKU or UPC); human-readable field is a clean product-name
  string (e.g. `Flavor A 32oz ea`).

### Join-key ladder — use the highest rung that exists

1. **Internal item number / SKU series** — the customer's own
   product-number scheme. When it appears on both sides, join
   directly (exact match, highest confidence). Usually the backbone
   of the crosswalk. This is also the value that becomes
   `drivepointMappedSku`.
2. **Consumer UPC / GTIN** — the barcode on the physical unit. Use
   it when a channel lacks the internal number, or to CONFIRM an
   item-number match. UPCs are per-size, so they cleanly
   disambiguate two sizes of the same base product.
   > **Do not trust UPC blindly.** UPCs are occasionally reused
   > across products, mistyped, or truncated (check-digit stripped
   > in one system, kept in another). Always confirm a UPC-only
   > match against brand + normalized title + size. A 12-digit
   > value sitting in an item-number field is usually a UPC, not an
   > item number.
3. **Name / shelf-label semantics** — parse flavor/variant + form +
   size out of free text. The only option for a channel with no
   SKU/UPC, and for orphan rows. Weakest rung — always flag a
   name-only match as `unmapped`.

Legacy retailer-specific codes are often the same product under a
superseded label — map via the size/flavor embedded in the code,
anchored on the shared internal item number where one exists.

---

## Always flag for confirmation — never silently guess

Present the map as a first pass. Mark anything uncertain as
`unmapped` (omit the patch) and call it out in the review table, at
minimum:

- Opaque codes decoded only by inference (price, family pattern,
  timing).
- Name-only matches, especially a flavor/variant/format the other
  channels don't have.
- UPC-only matches that couldn't be corroborated against title +
  size.
- Size or pack-count collapses (multiple real variants rolled into
  one canonical — offer to split).
- Bundles and kits.
- SKU reuse across eras.
- Display/sample/non-product SKUs (use `rejected` and ask whether to
  drop).
- Channel-only presence (a product seen in just one channel —
  confirm it's real, not a feed gap).

---

## Presenting the result

The artifact is a **projection** of the in-head decision set you
committed to in step 7 — it aggregates for human review, but the
underlying data is still one decision per sourceKey. When you save
in step 10, you serialize that same in-head set directly; the
artifact is never the source of truth. **Emit the JSX inline** —
do not spawn a `code_execution` script to reshape the canonical
list into artifact-ready data. You already have the list; hand it
straight to the component.

Render ONE JSX/React artifact (`application/vnd.ant.react`)
containing three sections. Do NOT render one row per source row — on
a 500+ row roster that is thousands of cells of transcription and
nobody reviews it.

1. **Canonical products** — one row per canonical. Columns:
   `drivepointMappedId`, `drivepointMappedProductName`,
   `drivepointMappedSku`, `productFamily`, `productCategory`,
   `productFormat`, `sizeVariant`, `sourceRowCount`, `channels`
   (comma-separated). `sourceRowCount` is the count of aliases from
   the step-7 set that share this canonical — a reminder to yourself
   that each of those aliases becomes its own CSV row on save.
2. **Flagged rows** — one row per flagged source row. Columns:
   `channel`, `stores`, `sku`, `title`, `proposedCanonical`,
   `reasonFlagged`. Visually distinguish this section from Canonical
   products (e.g. tinted row background).
3. **Coverage summary** — one row per channel. Columns: `channel`,
   `totalRows`, `confirmed`, `rejected`, `unmapped`.

**Styling.** Fetch the `artifact-style-guide` skill via `get_skill`
and follow its tokens so the table matches the server's other
artifacts.

**End your turn here.** Ask the user to review and reply with
`save` / `looks good` / `proceed` / `publish` to write, or to tell
you what to change. **Do NOT call `save_product_mappings_to_firebase`
on the same turn as the artifact.** See "Approval gate — DO NOT SKIP"
above; save is step 10, and only after explicit approval.

---

## Never do

- **Never split the read.** One `read_product_mapping_source` call
  per session. Do not call it per channel, per SKU prefix, or per
  anything else. If the roster is too large to reason about in one
  context, ask the user which subset to focus on rather than issuing
  multiple reads.
- **Never try to re-materialize the roster as a file.** Your script
  environment cannot access the tool response — the roster only
  exists in your context. Do not spend turns hand-typing 500+ rows
  into records.json / records.tsv via shell echo/append commands so
  a "decision engine" script can read them. That is not the fastest
  path, it is the slowest one — you burn tokens transcribing data
  you already have. Reason inline; scripts are for CSV serialization
  at the end, not for the mapping decisions themselves.
- **Never write a "decision engine" or "grouping algorithm" script.**
  The mapping decisions are inline judgment (normalize → block →
  group → assign id → pick values) against the roster in your
  context. If you find yourself designing a pipeline, stop —
  reasoning against the roster directly is dramatically faster than
  building infrastructure to reason for you.
- **Never run exploratory `code_execution` on the roster.** After
  `read_product_mapping_source` succeeds, the roster is context you
  read directly. Do not spawn scripts named "inspect structure",
  "preview payloads", "summarize statuses/channels", "list existing
  canonicals", "dump unmapped rows", "check stores dimension", "list
  previously rejected rows", "see confirmed sourceKeys per canonical",
  or "sample Amazon titles for disambiguation" — every one of those is
  inline reading of context you already have, and each round-trip is
  10-30 seconds of overhead for zero new information. If you feel the
  urge to script an EDA pass, that is the signal to re-read the
  roster in context and start deciding, not the signal to open a
  shell.
- **Never invent a `drivepointMappedId`.** Always derive it from
  `slug(productFamily) + '-' + slug(flavor/variant) + '-' + slug(sizeVariant)`.
- **Never invent a name, SKU, or description.** Every value in
  `drivepointMappedProductName`, `drivepointMappedSku`, and
  `productDescription` must come from a source row (verbatim or after
  the normalization rules above). Prefer null over a plausible
  guess.
- **Never let two rows share a `drivepointMappedId` but disagree on
  name/family/category/format/size.** Those are canonical attributes;
  decide them once per canonical, then repeat verbatim across every
  alias in the CSV. On re-runs, unchanged aliases stay in Firestore
  untouched — a merge, not an overwrite — so they stay in lockstep
  for free without needing to re-emit them.
- **Never collapse discriminating variants.** Different sizes,
  different pack counts, different flavors are DIFFERENT canonical
  products — even if the base name is identical. Splitting real
  variants is not optional.
- **Never trust a UPC-only match without corroboration.** UPCs get
  reused, mistyped, and truncated. Confirm against brand + title +
  size before using UPC alone.
- **Never echo source-context columns into the save CSV.** `channel`,
  `stores`, `sku`, `title`, `productType` are rehydrated server-side
  from `sourceKey`. Including them as columns wastes tokens and will
  be ignored.
- **Never send CSV rows for `unmapped` source rows.** Omit them
  entirely; the server records them as `unmapped` by default.
- **Never JSON-encode the `mappings` argument itself.** `mappings` is
  a **CSV string** — header row + data rows, emitted directly. Do
  not wrap it in an array, do not JSON-encode the values.
  `rejected_source_keys` IS a JSON array of strings — those are two
  different arguments with two different shapes.
- **Never build the CSV with naive `join(",")`.** Titles/sourceKeys
  can contain commas. Use a real CSV library (Python `csv`, Node
  `csv-stringify`) OR quote every field that contains a comma /
  double quote / newline with `"..."` and escape embedded quotes as
  `""`. Silent truncation on the first comma-containing row is the
  most common data-corruption bug in this workflow.
- **Never re-emit unchanged confirmations on a re-run.** Save is a
  merge — rows you don't mention keep their prior state in Firestore
  automatically. Re-sending the full 500-row baseline every save
  bloats the payload for zero benefit and costs 60-90 seconds of
  generation time.
- **Never re-enumerate aliases at save time.** If step 10 starts with
  "let me scan the roster and figure out which sourceKeys belong to
  the cucumber balm canonical" — stop. You skipped step 7. The
  per-sourceKey decision set was supposed to be built once, before
  the artifact, and the save is a straight serialization of it. If
  the artifact only lists one representative per canonical and you're
  hitting the "which aliases go on this canonical?" question at save
  time, the mapping decisions never got materialized — go back and
  redo step 7 (in your head, not as scratch text) so save is a pure
  transcription pass.
- **Never call `code_execution` to build the artifact's row data.**
  You already have the canonicals inline from step 7; pass them
  directly into the JSX. Spawning a script just to reshape a 30-item
  array into artifact-ready JSON is a 30-60s round-trip that buys
  nothing.
- **The only justified `code_execution` call in this whole workflow
  is the ONE RFC-4180 CSV writer at save time**, and only when the
  CSV is large enough that manual quoting is error-prone (roughly
  100+ rows). Even then, it is **one** call — build the CSV and emit
  the tool call in the same turn. Do NOT chain a "verify byte size",
  "preview first 20 rows", "re-read the CSV back into memory", or
  any other follow-up script — each of those is a separate 10-30s
  round-trip for information you can already see. Small saves
  (<100 rows) should be emitted inline without any script at all.
- **Never write step 7 out as scratch text.** The per-sourceKey
  decision set is meant to be held in context, not printed as
  hundreds of `sourceKey → decision` lines before the artifact.
  Writing it out costs the same output tokens as sending the actual
  save CSV twice — once as scratch, once at save — for zero benefit.
  You know the mapping; commit to it inline and move to the artifact.
- **Never emit a `confirmed` row with empty mapped-\* / product-\*
  fields.** Every confirmation must carry its full attribute set. The
  server drops fieldless confirmations and reports them under
  `invalidConfirmedCount` — a non-zero value means you tried a
  shortcut that no longer exists under merge semantics. Supply the
  fields and re-save.
- **Never CSV a pure reject.** If a row is being rejected with no
  fields to spell out, put its sourceKey in `rejected_source_keys`
  instead. A row of `key,rejected,,,,,,,` is 40+ characters of
  filler for something that could be one string in a JSON array.
- **Never silently omit a row to try to undecide it.** Under merge
  semantics, omission means "leave as-is." To demote a previously
  confirmed or rejected row back to `unmapped`, list its sourceKey in
  `unmapped_source_keys` — that's the only way the server knows to
  delete the prior decision.
- **Never call `save_product_mappings_to_firebase` without prior
  explicit user approval.** See "Approval gate — DO NOT SKIP". The
  artifact-and-immediately-save pattern is a protocol violation, no
  matter how confident you are in the mappings.
- **Never silently map a bundle as a single simple unit.** Flag it
  and ask.
- **Never re-save just to retry publish.** If `publish` fails after a
  successful `save`, rerun `publish` only — Firestore already has the
  right state.

---

## Reference — consult only when resolving a flagged row

Do not read this section on the main path. It exists for the handful
of rows the procedure above can't resolve cleanly.

**Decoding an internal item-number scheme.** Many customers encode
flavor/variant, form, and size/pack into the number itself (leading
digits = line + flavor, trailing digits = size + pack). Decode it by
cross-referencing DTC titles against retailer shelf labels for the
same number — a DTC "Flavor A, 1-Pack" and a shelf label
"BRAND 32OZ FLAVOR A" on the same number pin down family + size.
Don't assume trailing digits are only pack-count; they often encode a
genuinely different size. Split real size differences into separate
canonical products; only roll up pure pack-count variants if the
customer wants product-level grain. Always confirm a decoded number
against the shelf label + UPC — never trust the numeric pattern
alone.

**Patterns that bite:**

- **A 12-digit value sitting in an item-number field is usually a
  UPC**, not an item number — detect it because it doesn't match the
  customer's normal pattern.
- **Legacy retailer-specific codes** are often the same product
  under a superseded label — map via the size/flavor embedded in the
  code, anchored on the shared internal item number where one
  exists.
- **A channel with no SKU or UPC at all is a name-only match, full
  stop** — flag every row resolved there.
- **Channel coverage is not uniform.** A product legitimately present
  in one channel and absent from another is a real gap, not a
  mapping miss — don't force a match where none exists.
- **When in doubt, the UPC decides** — but only after you've
  corroborated it against brand + normalized title + size. Build a
  UPC → canonical lookup from whichever channel has the cleanest UPC
  data and use it to confirm item-number matches and rescue UPC-only
  rows.
- **GTINs with and without the check digit** can look like different
  identifiers (`012345678901` vs. `12345678901`). When comparing
  UPCs across channels, strip leading zeros and the check digit if
  one side is 12 digits and the other is 11 or 13.
