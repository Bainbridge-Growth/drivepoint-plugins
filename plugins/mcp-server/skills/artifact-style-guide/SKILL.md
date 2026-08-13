---
name: artifact-style-guide
description: Visual rules for Drivepoint React artifacts - brand lockup, color tokens, typography, number formatting, chart-type selection, layout patterns, the Recharts tooltip pattern, and artifact data-hygiene rules. Use whenever producing or restyling a chart, dashboard, or visual artifact from a query result, and when deciding whether a result warrants an artifact at all rather than a text answer. Covers the Recharts plus Tailwind plus lucide-react stack and how to link an artifact back to an existing Drivepoint report.
---

# Artifact Style Guide

Visual rules for React artifacts. Inline-tokenized from the Drivepoint brand
system so this file is self-contained.

---

## When to create an artifact

- "Show me", "chart", "visualize", "dashboard", "trend", "compare",
  "breakdown" → React artifact.
- A simple factual question with ≤5 rows or 1 dimension → text answer with
  the supporting SQL.
- A result with >5 rows or ≥2 dimensions → suggest or produce a
  visualization.

When in doubt, produce the artifact AND show the SQL underneath.

---

## Technology

- React functional components with hooks.
- **Recharts** for charts (`LineChart`, `BarChart`, `ComposedChart`,
  `ResponsiveContainer`, `Tooltip`, etc.).
- **Tailwind** utility classes only — no custom config, no `@apply`.
- **lucide-react** for icons (small, optional).
- All data is hardcoded into the component from the query result. No fetch,
  no external APIs.
- Artifact MIME type: `application/vnd.ant.react`.

Do not load Google Fonts, CDN scripts, or any external resource.

---

## Brand lockup

Every React artifact opens with the Drivepoint lockup — mark + wordmark —
paired with the title block. Use the `ArtifactHeader` component below as
the first child of the outer container. Do not draw a custom title row.

### Sizing

- Mark: 24px square.
- Wordmark: 16px tall.
- These defaults balance against a `text-lg` title. Do not enlarge.

### Surface

The wordmark below is dark text for light backgrounds, which is the only
surface artifacts use today (`bg-white`, transparent). If a dark surface
is ever introduced, the wordmark must be swapped for the inverse variant
— out of scope here, flag and stop.

### Components

Path data is character-exact from the Drivepoint brand source. Do not
modify, reorder, or re-pretty-print the path strings — one stray
character breaks the brand color split. After pasting, render the
lockup once standalone and eyeball it against a known-good reference
before propagating to a full artifact.

If the SVG fails to render cleanly, **do not ship broken artwork** —
fall back to the text-only string `Drivepoint` in
`text-slate-900 font-semibold tracking-tight` as the wordmark and omit
the mark.

```jsx
const DrivepointMark = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 1000 1000" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
    <path d="M759.561 156.165L501.552 95.4526L294.435 46.7212L102.114 197.892L309.242 246.623L567.373 307.235L567.362 307.246L759.561 156.176V156.165Z" fill="#76A4EA"/>
    <path d="M759.583 156.173L757.621 421.22L756.059 634.001L563.738 785.171L565.311 572.391L567.384 307.255L567.362 307.244L759.561 156.173H759.583Z" fill="#5B8DD8"/>
    <path d="M893.874 324.268L635.865 263.556L428.748 214.825L236.427 365.995L443.555 414.727L701.675 475.339V475.35L893.874 324.279V324.268Z" fill="#FFDE6A"/>
    <path d="M893.886 324.282L891.936 589.34L890.362 802.109L698.041 953.279L699.625 740.499L701.687 475.364L701.676 475.352L893.875 324.282H893.886Z" fill="#E1BD3D"/>
  </svg>
);

const DrivepointWordmark = ({ height = 16 }) => (
  <svg height={height} viewBox="0 0 144 45" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" focusable="false">
    <path d="M8.8045 32.073H0.700928V11.4859H8.8045C12.0295 11.4859 14.6485 12.4324 16.6616 14.3255C18.6952 16.2185 19.712 18.7083 19.712 21.7949C19.712 24.8814 18.7054 27.3712 16.6924 29.2643C14.6793 31.1367 12.05 32.073 8.8045 32.073ZM8.8045 28.2148C10.7765 28.2148 12.3376 27.5975 13.4879 26.3629C14.6588 25.1283 15.2442 23.6056 15.2442 21.7949C15.2442 19.9018 14.6793 18.3585 13.5496 17.1651C12.4198 15.951 10.8381 15.344 8.8045 15.344H5.07624V28.2148H8.8045Z" fill="#333333"/>
    <path d="M26.6377 32.073H22.7246V17.1651H26.6377V19.2022C27.1923 18.5026 27.901 17.9264 28.7637 17.4737C29.6265 17.021 30.4995 16.7947 31.3828 16.7947V20.622C31.1157 20.5602 30.7563 20.5294 30.3044 20.5294C29.647 20.5294 28.9486 20.694 28.2091 21.0232C27.4696 21.3525 26.9458 21.7537 26.6377 22.227V32.073Z" fill="#333333"/>
    <path d="M35.7689 15.5601C35.1321 15.5601 34.5775 15.3337 34.1051 14.881C33.6532 14.4078 33.4272 13.8522 33.4272 13.2143C33.4272 12.5764 33.6532 12.0311 34.1051 11.5785C34.5775 11.1258 35.1321 10.8994 35.7689 10.8994C36.4262 10.8994 36.9809 11.1258 37.4328 11.5785C37.8847 12.0311 38.1106 12.5764 38.1106 13.2143C38.1106 13.8522 37.8847 14.4078 37.4328 14.881C36.9809 15.3337 36.4262 15.5601 35.7689 15.5601ZM37.7409 32.073H33.8278V17.1651H37.7409V32.073Z" fill="#333333"/>
    <path d="M49.6938 32.073H45.4726L39.495 17.1651H43.6855L47.5678 27.5358L51.4501 17.1651H55.6714L49.6938 32.073Z" fill="#333333"/>
    <path d="M64.4126 32.4434C62.112 32.4434 60.2119 31.7232 58.7124 30.2828C57.2128 28.8424 56.4631 26.9494 56.4631 24.6036C56.4631 22.4019 57.182 20.55 58.6199 19.0478C60.0784 17.5457 61.9271 16.7947 64.1661 16.7947C66.3846 16.7947 68.1819 17.556 69.5582 19.0787C70.9345 20.5808 71.6226 22.5562 71.6226 25.0048V25.8691H60.5611C60.6843 26.8568 61.126 27.6798 61.886 28.3383C62.646 28.9968 63.632 29.326 64.844 29.326C65.5013 29.326 66.21 29.1922 66.97 28.9247C67.7506 28.6572 68.3668 28.2971 68.8187 27.8445L70.5442 30.3754C69.0447 31.7541 67.0008 32.4434 64.4126 32.4434ZM67.8327 23.2147C67.7711 22.371 67.4322 21.6097 66.8159 20.9306C66.2202 20.2516 65.337 19.9121 64.1661 19.9121C63.0569 19.9121 62.1941 20.2516 61.5779 20.9306C60.9616 21.5891 60.6022 22.3504 60.4995 23.2147H67.8327Z" fill="#333333"/>
    <path d="M82.9533 32.4434C81.084 32.4434 79.5537 31.682 78.3623 30.1594V37.7522H74.4491V17.1651H78.3623V19.0478C79.5331 17.5457 81.0635 16.7947 82.9533 16.7947C84.9047 16.7947 86.4864 17.4943 87.6983 18.8935C88.9308 20.2722 89.5471 22.1755 89.5471 24.6036C89.5471 27.0317 88.9308 28.9453 87.6983 30.3445C86.4864 31.7438 84.9047 32.4434 82.9533 32.4434ZM81.7208 28.9556C82.8506 28.9556 83.7544 28.5544 84.4323 27.7519C85.1307 26.9494 85.4799 25.8999 85.4799 24.6036C85.4799 23.3278 85.1307 22.2887 84.4323 21.4862C83.7544 20.6837 82.8506 20.2825 81.7208 20.2825C81.084 20.2825 80.4472 20.4471 79.8104 20.7763C79.1737 21.1055 78.6909 21.5068 78.3623 21.98V27.258C78.6909 27.7313 79.1737 28.1325 79.8104 28.4618C80.4678 28.791 81.1046 28.9556 81.7208 28.9556Z" fill="#333333"/>
    <path d="M105.046 30.1902C103.608 31.6923 101.698 32.4434 99.3147 32.4434C96.9319 32.4434 95.0216 31.6923 93.5837 30.1902C92.1663 28.6675 91.4576 26.8053 91.4576 24.6036C91.4576 22.4019 92.1663 20.55 93.5837 19.0478C95.0216 17.5457 96.9319 16.7947 99.3147 16.7947C101.698 16.7947 103.608 17.5457 105.046 19.0478C106.484 20.55 107.203 22.4019 107.203 24.6036C107.203 26.8053 106.484 28.6675 105.046 30.1902ZM96.5416 27.721C97.2195 28.5441 98.1439 28.9556 99.3147 28.9556C100.486 28.9556 101.41 28.5441 102.088 27.721C102.786 26.8773 103.135 25.8382 103.135 24.6036C103.135 23.3896 102.786 22.371 102.088 21.5479C101.41 20.7043 100.486 20.2825 99.3147 20.2825C98.1439 20.2825 97.2195 20.7043 96.5416 21.5479C95.8638 22.371 95.5248 23.3896 95.5248 24.6036C95.5248 25.8382 95.8638 26.8773 96.5416 27.721Z" fill="#333333"/>
    <path d="M112.047 15.5601C111.41 15.5601 110.855 15.3337 110.383 14.881C109.931 14.4078 109.705 13.8522 109.705 13.2143C109.705 12.5764 109.931 12.0311 110.383 11.5785C110.855 11.1258 111.41 10.8994 112.047 10.8994C112.704 10.8994 113.259 11.1258 113.711 11.5785C114.163 12.0311 114.389 12.5764 114.389 13.2143C114.389 13.8522 114.163 14.4078 113.711 14.881C113.259 15.3337 112.704 15.5601 112.047 15.5601ZM114.019 32.073H110.106V17.1651H114.019V32.073Z" fill="#333333"/>
    <path d="M131.857 32.073H127.944V23.0603C127.944 21.2084 127.03 20.2825 125.201 20.2825C123.784 20.2825 122.654 20.8689 121.812 22.0418V32.073H117.899V17.1651H121.812V19.1096C123.106 17.5663 124.842 16.7947 127.019 16.7947C128.622 16.7947 129.823 17.2165 130.624 18.0602C131.446 18.9038 131.857 20.0664 131.857 21.5479V32.073Z" fill="#333333"/>
    <path d="M140.734 32.4434C139.358 32.4434 138.31 32.0936 137.591 31.394C136.872 30.6943 136.513 29.6861 136.513 28.3692V20.5911H134.048V17.1651H136.513V13.0908H140.457V17.1651H143.476V20.5911H140.457V27.3197C140.457 27.793 140.58 28.184 140.826 28.4926C141.073 28.8013 141.401 28.9556 141.812 28.9556C142.429 28.9556 142.88 28.8116 143.168 28.5235L144 31.4866C143.281 32.1244 142.192 32.4434 140.734 32.4434Z" fill="#333333"/>
  </svg>
);

const ArtifactHeader = ({ title, subtitle }) => (
  <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
    <div className="min-w-0">
      <div className="text-lg font-semibold text-slate-900 mb-1">{title}</div>
      <div className="text-sm text-slate-500">{subtitle}</div>
    </div>
    <div className="flex items-center gap-2 shrink-0" role="img" aria-label="Drivepoint">
      <DrivepointMark />
      <DrivepointWordmark />
    </div>
  </div>
);
```

`flex-wrap` + `gap-3` lets the lockup drop below the title block on narrow
viewports without colliding. `min-w-0` on the title block lets long
titles truncate or wrap rather than push the lockup off-screen.

---

## Color tokens

Primary:
- `#5b8dd8` — Drivepoint blue (primary series)
- `#76A4EA` — light blue (secondary)
- `#FFDE6A` — Drivepoint yellow (accent)
- `#E1BD3D` — dark yellow (secondary accent)

Series order (use in this sequence when mapping channels or categories):
1. `#5b8dd8`
2. `#E1BD3D`
3. `#76A4EA`
4. `#64748b`
5. `#94a3b8`
6. `#cbd5e1`

Semantic:
- Positive / favorable: `#22c55e`
- Negative / unfavorable: `#ef4444`
- Neutral / zero: `#94a3b8`
- Forecast (when contrasted with actual): `#cbd5e1` (lighter than the
  actual-series color, with reduced opacity or a dashed stroke)

Surface:
- Background: transparent (inherit from Claude UI)
- Card background: `#ffffff` with `border border-slate-200 rounded-lg shadow-sm`
- Body text: `#1e293b`
- Muted text: `#64748b`

Never use color as the only encoder for sign or variance. Pair color with
an arrow, sign, or label.

---

## Typography

- System font stack — never load fonts.
- Headers: `font-semibold`. Use `text-base` for chart titles and `text-xl`
  for dashboard headers.
- Body: default Tailwind base.
- Numbers in tables: `tabular-nums` and right-aligned.

---

## Number formatting

Currency — always include the currency code, never assume USD:

```js
const fmtMoney = (n, currency = 'USD') =>
  new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(n);
```

The `currency = 'USD'` default is a defensive fallback only. Always pass
the real currency from the query result.

Percentages — one decimal place:

```js
const fmtPct = (n) => `${(n * 100).toFixed(1)}%`;
// or, if values are already in % units: `${n.toFixed(1)}%`
```

Negative financial values — parentheses, not minus sign:

```js
const fmtFinancial = (n, currency = 'USD') => {
  const abs = Math.abs(n);
  const s = fmtMoney(abs, currency);
  return n < 0 ? `(${s})` : s;
};
```

Large counts — thousands separator:

```js
const fmtCount = (n) => new Intl.NumberFormat('en-US').format(n);
```

---

## Chart-type selection

| Data shape | Chart type |
|---|---|
| Single series over time | Area chart |
| 2–4 series over time | Line chart |
| Comparison across ≤8 categories | Horizontal bar |
| Ranking (top N) | Horizontal bar, sorted descending |
| Part of whole, 2–5 segments | Donut |
| Part of whole, over time | Stacked bar |
| Two metrics on different scales | `ComposedChart` with two Y axes |
| Actuals vs. forecast | Grouped bar (solid actual, lighter / dashed forecast) |
| Variance | Diverging bar (green right, red left) |
| Multi-KPI snapshot | Card grid (3–4 across) |

Never use:
- Pie charts with >5 slices
- 3D anything
- Default Recharts colors
- Rainbow palettes — series hierarchy comes from the primary/secondary
  token order, not from hue distinctiveness

---

## Layout patterns

- Outer container: `p-6 bg-white`. First child is
  `<ArtifactHeader title={…} subtitle={…} />` (see § "Brand lockup").
  The `subtitle` prop contains the date range, plan (if SmartModel),
  channel filter, and currency — all on one line, separated by `·`.
- Dashboards: card grid for KPIs across the top (2–4 columns on desktop,
  stack on narrow), main chart below, supporting table at the bottom.
- Chart container: `<ResponsiveContainer width="100%" height={360}>`
  (≥320, ≤480 in practice).
- Tables: sticky header (`sticky top-0 bg-white`), zebra stripes
  (`even:bg-slate-50`), right-aligned numeric columns.
- Always include a small footer line: `<div className="text-xs text-slate-400
  mt-4">Source: {{env_prefix}}_dwh_mart · <table names></div>`.

---

## Data hygiene rules for artifacts

1. If the result has >25 rows, show top 25 and a single "Others" row that
   sums the tail. Show the count in the subtitle.
2. If values span >2 orders of magnitude, either log-scale the axis or split
   into two charts. Never let a $50M line and a $5K line share a linear
   axis.
3. If multiple currencies are present, render one chart per currency or
   show currency on every cell. Never combine.
4. Show date range, plan name (if SmartModel), channel filter, and currency
   in the subtitle of every artifact.
5. Surface nulls and zeros — do not silently drop rows. If a metric is
   missing for a month, show the gap in the chart.
6. **Never display raw shipping addresses** (`address1`, `address2`) from
   the line-item table. Aggregate to city, province, or country.
7. **Derive currency from the query result.** Never hardcode `'USD'` in an
   artifact rendered for a real user. The synthetic-data examples in
   `example-artifacts.md` set `CURRENCY` from the data — copy that pattern.

---

## Linking to existing Drivepoint reports

**If `report-catalog.md` is not present in Knowledge, set
`REPORT_LINK = null` for every artifact** — the footer block below
short-circuits on null and renders nothing. Don't fabricate a link or
guess a bundle ID.

When the catalog IS present and a bundle matches the question's intent,
render a link footer above the data-source line. Use this pattern:

```jsx
// At the top of the component:
const COMPANY_ID = '<resolved from the query result — never hardcode>';
// Set to null if no stock bundle matches the question's intent.
const REPORT_LINK = {
  name: 'Financial Statements',
  url: `https://app.drivepoint.io/${COMPANY_ID}/reports/bundle/finance_bundle`,
};

// In the JSX, just above the source footer:
{REPORT_LINK && (
  <div className="text-xs text-slate-500 mt-4">
    📊 Also available in Drivepoint:{' '}
    <a
      href={REPORT_LINK.url}
      target="_blank"
      rel="noopener noreferrer"
      className="text-slate-700 underline hover:text-slate-900"
    >
      {REPORT_LINK.name}
    </a>
  </div>
)}
<div className="text-xs text-slate-400 mt-2">
  Source: {{env_prefix}}_dwh_mart.<table>
</div>
```

Rules:
- `REPORT_LINK` shape: `{ name: string, url: string } | null`.
- Set to `null` (and omit the footer) if no bundle is a clean intent match.
  Don't render a generic "go to Reports" link on every artifact.
- `COMPANY_ID` comes from the query result's `company_id` column. Never
  hardcode it.

---

## Tooltip pattern (Recharts)

```jsx
const ChartTooltip = ({ active, payload, label, currency = 'USD' }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded shadow-sm p-3 text-sm">
      <div className="font-semibold text-slate-900 mb-1">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-slate-600">{p.name}:</span>
          <span className="tabular-nums text-slate-900">{fmtMoney(p.value, currency)}</span>
        </div>
      ))}
    </div>
  );
};
```
