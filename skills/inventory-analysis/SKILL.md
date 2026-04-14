---
name: inventory-analysis
description: Analyze inventory health — weeks of supply, stockout risk, dead stock, and reorder timing. Use when a user asks about inventory levels, "how much inventory do we have?", "are we at risk of stocking out?", "what's our weeks of supply?", "dead stock", "overstock", or "inventory management". Also triggers on "WOS", "inventory turn", "days of inventory", "stockout risk", or "safety stock".
---

# Inventory Analysis

**Purpose**: Assess inventory health across SKUs — identifying stockout risk, overstock / dead-stock positions, and reorder timing relative to sales velocity and lead times.
**Prerequisite**: The `smartmodel-protocol` skill must be loaded.

---

## When This Skill Activates

- User asks about inventory levels or inventory health
- User wants to know weeks of supply or stockout risk
- User asks about dead stock or overstock positions
- User is planning reorders and wants to know when to order
- User is evaluating working capital tied up in inventory

---

## Phase 1 — Orient

**Step 1.1 — Read model identity**
Call `read_smartmodel_settings` → capture `settings.companyName`, `settings.currency`.

**Step 1.2 — Locate inventory data**
Call `read_smartmodel_index` → identify sheets or R- sheets that contain inventory data. Look for template IDs or sheet names related to inventory, supply chain, or operations.

**Step 1.3 — Check data availability**
Call `read_r_sheet` on any inventory R- sheets → verify if current inventory on-hand data is populated. Inventory analysis requires:
- Current units on hand by SKU
- Sales velocity (units sold per period)
- Optionally: lead times, safety stock targets, reorder points

**Step 1.4 — Read time context**
Call `read_smartmodel_date_spine` → determine the most recent Actual period for sales velocity calculation.

---

## Phase 2 — Gather Data

Call `read_smartmodel_data_section` on inventory and channel sheets:

| Data Point | Source | Identifier pattern |
|-----------|--------|-------------------|
| Units on hand | Inventory sheet or R- sheet | `inventory_oh`, `units_oh`, `on_hand` |
| Units sold (actuals) | Channel sheets | `units_sold`, `orders`, `units` |
| Units in transit | Inventory sheet | `in_transit`, `inbound_units` |
| Lead time (days) | Inventory sheet | `lead_time`, `supplier_lead_time` |
| Safety stock target | Inventory sheet | `safety_stock`, `min_stock` |
| Reorder point | Inventory sheet | `reorder_point`, `rop` |
| Forecast demand | Channel sheets | `units` in Forecast columns |

If inventory data isn't structured in the SmartModel, note this and ask if the user can provide a CSV or direct input of current on-hand quantities.

---

## Phase 3 — Compute

### Sales velocity

```
Average Weekly Units Sold = Total Units Sold (trailing 8 weeks) / 8
Average Monthly Units Sold = Average Weekly Units Sold × 4.33
```

Use trailing 8-week velocity as the baseline. Note if there are seasonal patterns that would make simple trailing average misleading.

### Weeks of Supply (WOS)

```
WOS = Units On Hand / Average Weekly Units Sold
```

Include in-transit units if lead time is shorter than current WOS:
```
WOS (with in-transit) = (Units On Hand + Units In Transit) / Average Weekly Units Sold
```

### Stockout risk classification

| WOS | Status | Action |
|-----|--------|--------|
| < 4 weeks | CRITICAL — stockout imminent | Expedite reorder immediately |
| 4–8 weeks | At risk | Place reorder now |
| 8–12 weeks | Watch | Monitor; reorder per normal schedule |
| 12–20 weeks | Healthy | No action needed |
| > 20 weeks | Overstock | Evaluate promotion or markdown |

Adjust thresholds based on declared lead time — a SKU with 12-week lead time needs earlier action.

### Reorder timing

```
Reorder Date = Today − Lead Time Days + (Safety Stock Weeks × 7)
Units to Order = (Forecast Demand × Target WOS) − Units On Hand − Units In Transit
```

Call `get_todays_date` to anchor reorder date calculations.

### Dead stock / slow-mover identification

Flag a SKU as dead stock if:
- WOS > 52 weeks (more than 1 year of supply)
- Units sold in the trailing 8 weeks = 0

Flag as slow-mover if:
- WOS > 26 weeks (more than 6 months of supply)
- Velocity has declined >40% from the prior 8-week period

### Working capital at risk

```
Inventory Value = Units On Hand × Unit Cost (from product sheet)
Excess Inventory Value = (Units On Hand − Target WOS × Weekly Velocity) × Unit Cost
```

---

## Phase 4 — Output

### Default output

1. **Headline**: "[N] of [total] SKUs are at stockout risk. [M] SKUs are overstocked, representing $[X] in excess inventory."
2. **Inventory health table**:

```
| SKU | On Hand | In Transit | WOS | Velocity/wk | Status | Action |
|-----|---------|-----------|-----|-------------|--------|--------|
```

3. **Stockout risk list**: Critical and at-risk SKUs with recommended order quantities and urgency
4. **Overstock / dead stock list**: Overstocked SKUs with excess inventory $ value and markdown/promo options
5. **Reorder schedule**: For healthy SKUs, when to place the next order based on velocity and lead time
6. **Working capital summary**: Total inventory value, excess inventory value, and % of inventory that is excess

### Excel output (if requested)

Call `create_sheet` with blue tab. Call `write_range` for the inventory health table. Call `conditional_format_range` to color-code WOS status (red = critical, orange = at risk, green = healthy, gray = overstock). Call `format_range` for number and currency formatting.

---

## Guardrails

- Never write to Actual columns
- Inventory analysis depends on current on-hand data being accurate — note if the data appears stale (last updated date if available)
- Do not fabricate velocity assumptions — if fewer than 4 weeks of sales data are available, note the limitation and caveat WOS calculations
- Confirm with user before writing output to the workbook

---

## Common Mistakes to Avoid

1. Don't use average velocity during peak season to project off-season needs — velocity is seasonal; adjust for known seasonality
2. Don't ignore in-transit inventory — for brands with long lead times, in-transit is a significant portion of available supply
3. Don't conflate WOS with safety — a SKU with 10 WOS and a 12-week lead time is actually at risk
4. Don't flag overstock without considering upcoming promotions or channel expansion — what looks like dead stock may be pre-built for a pending retail launch
5. Don't analyze inventory without unit cost context — 10,000 units of a $1 item is not the same problem as 10,000 units of a $50 item

---

## Integration with Other Skills

- **`/product_cost_analysis`**: Unit cost data needed for inventory value calculations
- **`/variance_analysis`**: Check if inventory build or depletion is per plan
- **`/sku_rationalization`**: Dead-stock SKUs are rationalization candidates
- **`/build_report`**: Include inventory health in operational or board reports
