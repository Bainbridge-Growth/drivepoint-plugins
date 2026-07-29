# Product Mapping

How to decide when two product records — from the same channel over
time, or from different channels — refer to the same physical product,
and how to record those decisions with the MCP product-mapping tools.

Reading this skill is required any time the user asks to "map
products", "reconcile products", "crosswalk SKUs across channels",
"deduplicate the catalog", "clean up the catalog", "match Amazon to
Shopify products", or names the product-mapping flow. This is the
Drivepoint equivalent of the industry's *product crosswalk / entity
resolution / master-data-reconciliation* workflow — the vocabulary
varies, the job is the same: one canonical product per physical unit,
every channel row tied back to it.

The MCP server exposes exactly three product-mapping tools:

- `read_product_mapping_source` — read-only; returns the cross-channel
  product roster (one row per `channel/stores/sku/title`) from the
  customer's BigQuery warehouse. Each record also carries an
  `existing` field: the last saved decision for that sourceKey (or
  `null` on first-run). The response's `existingMappingCount` tells
  you whether this is a re-run.
- `save_product_mappings_to_firebase` — writes the current decision
  set to the company's Firestore mapping document. Takes two inputs:
  `mappings` (a CSV string of confirmed/rejected decisions) and
  optional `rejected_source_keys` (a JSON array of sourceKeys to
  reject in bulk). **Each call fully OVERWRITES the doc — submit the
  complete decision set every time.**
- `publish_product_mappings_to_bigquery` — reads the confirmed
  decisions out of Firestore and **fully OVERWRITES** the mapped-
  products catalog table in BigQuery.

Everything else is out of scope. Do not use `run_query`, `list_tables`,
or any other data-catalog tool as part of a mapping — the source table
`product_mapping_source` is pre-unioned across channels by dbt, and
the tools above already query it.

---

## Two ideas to hold in your head (read this first)

Everything else in this skill is scaffolding around these two rules.
If you only remember two things, remember these:

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

If you catch yourself typing a title, SKU, or description that doesn't
appear (in any form) in the source roster, stop — you are inventing,
which corrupts the crosswalk.

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
- **Emit deltas, not the whole world.** In the save CSV, unchanged
  confirmed rows should appear as `sourceKey,confirmed` with every
  other column empty — the server inherits the previous mapped-* /
  product-* values from Firestore. See the "Inheritance on re-runs"
  subsection under "The save call" below.
- **Bulk-reject via `rejected_source_keys`, not CSV rows.** POS junk
  and promotional lines that were rejected last run stay rejected
  cheaply by listing their sourceKeys in the array param.
- **Focus your judgment on three groups:** (a) rows with
  `existing = null` (brand new since last run), (b) rows with
  `existing.status = unmapped` (previously flagged, still open),
  (c) rows whose source title/SKU has drifted since the previous
  mapping (rare, but happens with rebrands and marketplace edits).

On a first-run (all `existing = null`) the workflow is the same as it
has always been — derive everything, decide everything, emit
everything.

---

## The one workflow

Follow these steps in order. Never skip a step, never reorder them.

1. **Read ONCE.** Call `read_product_mapping_source` a single time
   for the entire roster. Do NOT split the read by channel, by key
   type, or by SKU presence. One read, one roster in context.
2. **Normalize titles and sizes in place.** As you read each row,
   mentally apply the normalization rules in the next section. Do not
   write a script for this — do it inline as you group.
3. **Block, then group.** Cluster rows first by an obvious grouping
   attribute (brand line / product family), then within each block
   group by normalized title + normalized size into candidate
   canonical products. Blocking keeps you from comparing every row to
   every other row and is how a human analyst actually does this.
4. **Assign each group a canonical id** using the derivation rule
   below. Never invent an arbitrary id.
5. **Select the canonical values** for each group — name, SKU,
   description, attributes — from the source rows themselves, using
   the rules in "Choosing the mapped values". Never fabricate.
6. **Resolve leftover rows** using the join-key ladder in Part 2:
   exact internal SKU, then UPC, then name semantics. Flag anything
   resolved by name semantics alone as `unmapped` (omit the patch).
7. **Present the canonical summary + flagged rows** as a JSX/React
   artifact (see "Presenting the result"). Do NOT render every source
   row.
8. **STOP. Wait for explicit user approval.** See the "Approval gate"
   block below — this is a hard stop, not a soft one.
9. **Call `save_product_mappings_to_firebase` ONCE**, passing the
   complete decision set as a **CSV string** (see "Compact CSV
   format"). **Overwrites the Firestore doc.**
10. **Call `publish_product_mappings_to_bigquery` ONCE.** **Overwrites
    the BigQuery catalog table.** If this call fails after save, rerun
    publish — the Firestore doc is already correct, do not re-save.

**Use whatever is fastest.** Reason inline against the roster, or
write a small script (normalize titles, group by size, dedupe SKUs,
serialize the CSV) — whichever gets you to a correct decision set
sooner. The only rule is that the CSV you eventually pass to
`save_product_mappings_to_firebase` is **RFC 4180 compliant**: quote
any field containing a comma, double quote, or newline with `"..."`,
and escape embedded quotes as `""`. If you script the serialization,
use a real CSV library (Python's `csv` module, Node's `csv-stringify`,
etc.) rather than raw `join(",")` — the naive form silently corrupts
any row whose title contains a comma.

---

## Approval gate — DO NOT SKIP

Between step 7 (render the artifact) and step 9 (call save) there is
a **hard stop**. The user reviews the artifact and explicitly tells
you to proceed. You do not save until they do.

- After rendering the artifact, your next message ends with a short
  prompt: *"Review the map above. Reply `save` (or `looks good`,
  `proceed`, `publish`) to write to Firestore, or tell me what to
  change."*
- **Do NOT call `save_product_mappings_to_firebase` on the same turn
  as the artifact.** The artifact is for the user's eyes, not a
  self-triggering signal.
- **Do NOT call save on a follow-up turn unless the user's latest
  message is an explicit approval.** A neutral message ("ok",
  "thanks", "cool") is NOT an approval — ask again. A request for
  changes is not an approval — regenerate the artifact.
- **Do NOT infer approval from your own confidence.** "I've validated
  the counts and everything looks right" is not a reason to save;
  it is a reason to *ask*.
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

| Source variants                                | Canonical |
| ---------------------------------------------- | --------- |
| `32 oz`, `32oz`, `32 fl oz`, `32-FL-OZ`        | `32oz`    |
| `2 lb`, `2LB`, `2 pound`, `2-lb`               | `2lb`     |
| `500 ml`, `500ML`, `500-ml`                    | `500ml`   |
| `12 ct`, `12-Pack`, `12 pack`, `Case of 12`    | `12pack`  |
| `Single`, `1-pack`, `each`                     | *omit*    |

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
  group. Null is *more useful* than a fabricated string — a null
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

These may be *derived* by cleaning/standardizing source values, but
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

## Compact CSV format

`save_product_mappings_to_firebase` takes a single `mappings`
argument: a **CSV string**, not an array of objects. Emit CSV
directly — do not JSON-encode it, do not wrap it in an array. Line 1
is the header, one data line per row you're marking `confirmed` or
`rejected`. **Omit rows you're leaving unmapped entirely; the server
records them as `unmapped` for you.**

**Columns (pick whichever subset you need; always include `sourceKey`
and `status`):**

- `sourceKey` — copy verbatim from the source row
  (`channel::stores::sku`, falling back to title). This is how the
  server rejoins your row to the source row. Required in every line.
- `status` — `confirmed` when you are sure; `rejected` to exclude
  the row (display/sample/non-product lines). Required in every
  line.
- `drivepointMappedId` — derived per the rule above. Required when
  `status = confirmed`; leave the cell empty for `rejected`.
- `drivepointMappedProductName` — selected per "Choosing the mapped
  values". Required when `status = confirmed`.
- `drivepointMappedSku` — selected per "Choosing the mapped values";
  empty cell when unknown.
- `productFamily`, `productCategory`, `productFormat`, `sizeVariant`,
  `productDescription` — per "Choosing the mapped values"; empty
  cell when unknown.

**An empty cell is null.** Two commas in a row (`,,`) is how you
mark "unknown / not applicable" for a column.

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

Only `confirmed` rows are materialized into the BigQuery catalog;
`unmapped` / `rejected` are saved for review but not published.

### Example

Header + a few confirmed rows (multiple source rows collapsing onto
the same canonical product) and one rejected row:

```csv
sourceKey,status,drivepointMappedId,drivepointMappedProductName,drivepointMappedSku,productFamily,productCategory,productFormat,sizeVariant
Shopify::Mad Rabbit::BALM-VAN,confirmed,tattoo-balm-vanilla-coconut,Tattoo Balm,BALM-VAN,Tattoo Balm,Targeted Tattoo Aftercare,Balm,
Shopify::Mad Rabbit::BALM-VAN-P,confirmed,tattoo-balm-vanilla-coconut,Tattoo Balm,BALM-VAN,Tattoo Balm,Targeted Tattoo Aftercare,Balm,
Shopify::Mad Rabbit::Vanilla Balm,confirmed,tattoo-balm-vanilla-coconut,Tattoo Balm,BALM-VAN,Tattoo Balm,Targeted Tattoo Aftercare,Balm,
Shopify::Mad Rabbit::2PK-B-VAN,confirmed,tattoo-balm-vanilla-coconut-2pack,Tattoo Balm,2PK-B-VAN,Tattoo Balm,Targeted Tattoo Aftercare,Balm,2pack
Amazon::Mad Rabbit::UNKNOWN,rejected,,,,,,,
```

Notice every row sharing `tattoo-balm-vanilla-coconut` has identical
name, SKU, family, category, format, and size — that's the "decide
once per canonical, repeat verbatim" rule. The 2-pack has its own
`drivepointMappedId` and its own SKU because it's a different
physical product. The rejected row still needs the trailing commas
so the field count matches the header.

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

Render ONE JSX/React artifact (`application/vnd.ant.react`)
containing three sections. Do NOT render one row per source row — on
a 500+ row roster that is thousands of cells of transcription and
nobody reviews it.

1. **Canonical products** — one row per canonical. Columns:
   `drivepointMappedId`, `drivepointMappedProductName`,
   `drivepointMappedSku`, `productFamily`, `productCategory`,
   `productFormat`, `sizeVariant`, `sourceRowCount`, `channels`
   (comma-separated).
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
above; save is step 9, and only after explicit approval.

---

## Never do

- **Never split the read.** One `read_product_mapping_source` call
  per session. Do not call it per channel, per SKU prefix, or per
  anything else. If the roster is too large to reason about in one
  context, ask the user which subset to focus on rather than issuing
  multiple reads.
- **Never invent a `drivepointMappedId`.** Always derive it from
  `slug(productFamily) + '-' + slug(flavor/variant) + '-' + slug(sizeVariant)`.
- **Never invent a name, SKU, or description.** Every value in
  `drivepointMappedProductName`, `drivepointMappedSku`, and
  `productDescription` must come from a source row (verbatim or after
  the normalization rules above). Prefer null over a plausible
  guess.
- **Never let two rows share a `drivepointMappedId` but disagree on
  name/family/category/format/size.** Those are canonical attributes;
  decide them once per canonical, then repeat verbatim.
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
- **Never send JSON to `save_product_mappings_to_firebase`.** The
  `mappings` argument is a CSV string — header row + data rows,
  emitted directly. Do not wrap it in an array, do not JSON-encode
  the values.
- **Never build the CSV with naive `join(",")`.** Titles/sourceKeys
  can contain commas. Use a real CSV library (Python `csv`, Node
  `csv-stringify`) OR quote every field that contains a comma /
  double quote / newline with `"..."` and escape embedded quotes as
  `""`. Silent truncation on the first comma-containing row is the
  most common data-corruption bug in this workflow.
- **Never call `save_product_mappings_to_firebase` without prior
  explicit user approval.** See "Approval gate — DO NOT SKIP". The
  artifact-and-immediately-save pattern is a protocol violation, no
  matter how confident you are in the mappings.
- **Never silently map a bundle as a single simple unit.** Flag it
  and ask.
- **Never save partially and expect the doc to merge.** Each call to
  `save_product_mappings_to_firebase` fully OVERWRITES the previous
  set. Submit the complete decision set every time.
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
