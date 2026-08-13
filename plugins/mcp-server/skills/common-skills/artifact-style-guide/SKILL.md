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
- A structured reference or instruction document with **no charts and no
  numeric series** (e.g. model update guide, workbook field map) → React
  artifact using Example 8 in `example-artifacts.md`. If the answer has
  numbers to chart or table, use `report-creation-guide.md` instead.

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

## Two tiers

| Tier | Who builds it | Chrome |
|---|---|---|
| **Sent docs** | Drivepoint → customer (showcase, renewal, monthly, kickoff) | Full lockup masthead via `ArtifactHeader` + `ArtifactPage` + `SignatureFooter` |
| **Customer-built** | Customer's own Claude session (this connector) | Compact header + `BuiltWithFooter` — **no lockup in the header**, Drivepoint-only (no client accent colors) |

This skill's MCP path is **customer-built**. Sent-doc chrome stays documented
below so the components stay in one place; do not use it for connector
artifacts. Attribution on customer-built work comes from the chart palette
and the muted status pair (`#2f7d54` / `#b0472f`), plus the small footer —
not from co-brand accents or a masthead lockup.

---

## Brand lockup (sent docs only)

Sent docs open with the Drivepoint lockup on the **left**, optional
customer co-brand and meta, then the title block below a 1px hairline.
Use `ArtifactHeader` as the first child. Do not place the lockup on the
right. Do not compose `DrivepointMark` beside a separate wordmark SVG.

**Customer-built artifacts do not use this masthead** — use `CompactHeader`
instead (next section).

### Sizing

- Complete lockup (`DrivepointLockup`): height **27px** (viewBox `0 0 144 32`).
  Width scales from the viewBox. Do not enlarge.
- Mark alone (`DrivepointMark`): 13px in `BuiltWithFooter`; 24px for
  favicons / SVG-failure fallback only. Never pair it with typed
  "Drivepoint" as a header stand-in.

### Surface

The lockup below is the dark-text / light-background variant
(`bg-white`, transparent). If a dark surface is ever introduced, flag and
stop — an inverse lockup is out of scope here.

### Components

Path data is character-exact from the Drivepoint brand source. Do not
modify, reorder, or re-pretty-print the path strings — one stray
character breaks the brand color split.

If the lockup SVG fails to render cleanly, **do not ship broken artwork** —
fall back to `DrivepointMark` alone (24px square). Never render the
Drivepoint logotype as typed text in any font, and never pair the mark
with typed "Drivepoint".

On sent docs, `customer` and `meta` are optional.

```jsx
// Brand-locked: CI checks these against brand-contract.json. Brand changes
// come from the brand-core token set (drivepoint-internal-plugins), not from
// editing these lines.
const DrivepointMark = ({ size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 1000 1000" fill="none" aria-hidden="true" focusable="false">
    <path d="M759.561 156.165L501.552 95.4526L294.435 46.7212L102.114 197.892L309.242 246.623L567.373 307.235L567.362 307.246L759.561 156.176V156.165Z" fill="#76A4EA"/>
    <path d="M759.583 156.173L757.621 421.22L756.059 634.001L563.738 785.171L565.311 572.391L567.384 307.255L567.362 307.244L759.561 156.173H759.583Z" fill="#5B8DD8"/>
    <path d="M893.874 324.268L635.865 263.556L428.748 214.825L236.427 365.995L443.555 414.727L701.675 475.339V475.35L893.874 324.279V324.268Z" fill="#FFDE6A"/>
    <path d="M893.886 324.282L891.936 589.34L890.362 802.109L698.041 953.279L699.625 740.499L701.687 475.364L701.676 475.352L893.875 324.282H893.886Z" fill="#E1BD3D"/>
  </svg>
);

const DP_TEXT_PRIMARY = '#191815';
const DP_TEXT_MUTED = '#716e6b';
const DP_BORDER_SUBTLE = '#ecebe9';
const DP_CUSTOMER_PX = 16;
const DP_FONT_STACK = 'ui-sans-serif, system-ui, sans-serif';

const DrivepointLockup = ({ height = 27 }) => {
  const width = Math.round(height * 144 / 32);
  return (
    <svg width={width} height={height} viewBox="0 0 144 32" fill="none" aria-hidden="true" focusable="false">
      <path d="M23.1668 3.86317L14.0752 1.72014L6.77692 0L0 5.33607L7.29867 7.05621L16.3946 9.19572L16.3942 9.19611L23.1668 3.86356V3.86317Z" fill="#76A4EA"/>
      <path d="M23.1676 3.86353L23.0985 13.2192L23.0434 20.73L16.2665 26.0661L16.3219 18.5553L16.395 9.19646L16.3942 9.19607L23.1668 3.86353H23.1676Z" fill="#5B8DD8"/>
      <path d="M27.8996 9.79698L18.808 7.65395L11.5097 5.93381L4.73279 11.2699L12.0315 12.99L21.127 15.1295V15.1299L27.8996 9.79737V9.79698Z" fill="#FFDE6A"/>
      <path d="M27.9 9.79742L27.8313 19.1535L27.7758 26.6639L20.9989 32L21.0547 24.4892L21.1274 15.1304L21.127 15.13L27.8996 9.79742H27.9Z" fill="#E1BD3D"/>
      <path d="M47.6231 22.864H41.8463V8.18798H47.6231C49.9221 8.18798 51.7892 8.86274 53.2242 10.2123C54.6739 11.5618 55.3987 13.3367 55.3987 15.537C55.3987 17.7373 54.6812 19.5122 53.2462 20.8617C51.8111 22.1965 49.9368 22.864 47.6231 22.864ZM47.6231 20.1136C49.0289 20.1136 50.1418 19.6735 50.9618 18.7934C51.7965 17.9133 52.2138 16.8278 52.2138 15.537C52.2138 14.1875 51.8111 13.0873 51.0057 12.2365C50.2004 11.3711 49.0728 10.9384 47.6231 10.9384H44.9653V20.1136H47.6231Z" fill="#333333"/>
      <path d="M60.3359 22.864H57.5463V12.2365H60.3359V13.6887C60.7313 13.19 61.2365 12.7793 61.8515 12.4566C62.4665 12.1339 63.0889 11.9725 63.7185 11.9725V14.7009C63.5282 14.6569 63.2719 14.6349 62.9497 14.6349C62.4812 14.6349 61.9833 14.7522 61.4561 14.9869C60.929 15.2216 60.5555 15.5076 60.3359 15.845V22.864Z" fill="#333333"/>
      <path d="M66.8453 11.0924C66.3913 11.0924 65.996 10.931 65.6592 10.6083C65.337 10.2709 65.1759 9.87488 65.1759 9.42015C65.1759 8.96542 65.337 8.5767 65.6592 8.25399C65.996 7.93128 66.3913 7.76993 66.8453 7.76993C67.3139 7.76993 67.7092 7.93128 68.0314 8.25399C68.3535 8.5767 68.5146 8.96542 68.5146 9.42015C68.5146 9.87488 68.3535 10.2709 68.0314 10.6083C67.7092 10.931 67.3139 11.0924 66.8453 11.0924ZM68.251 22.864H65.4615V12.2365H68.251V22.864Z" fill="#333333"/>
      <path d="M76.7719 22.864H73.7627L69.5015 12.2365H72.4887L75.2563 19.6295L78.0239 12.2365H81.0331L76.7719 22.864Z" fill="#333333"/>
      <path d="M87.2645 23.128C85.6245 23.128 84.27 22.6146 83.201 21.5878C82.132 20.561 81.5975 19.2115 81.5975 17.5392C81.5975 15.9697 82.1101 14.6495 83.1351 13.5787C84.1748 12.5079 85.4927 11.9725 87.0888 11.9725C88.6703 11.9725 89.9516 12.5152 90.9327 13.6007C91.9138 14.6715 92.4043 16.0797 92.4043 17.8253V18.4414H84.5189C84.6068 19.1455 84.9216 19.7322 85.4634 20.2016C86.0052 20.671 86.7081 20.9057 87.572 20.9057C88.0406 20.9057 88.5458 20.8104 89.0876 20.6197C89.6441 20.429 90.0834 20.1723 90.4055 19.8496L91.6356 21.6538C90.5666 22.6366 89.1096 23.128 87.2645 23.128ZM89.7026 16.5491C89.6587 15.9477 89.4171 15.405 88.9778 14.9209C88.5531 14.4368 87.9235 14.1948 87.0888 14.1948C86.2981 14.1948 85.683 14.4368 85.2437 14.9209C84.8044 15.3903 84.5482 15.933 84.475 16.5491H89.7026Z" fill="#333333"/>
      <path d="M100.482 23.128C99.1491 23.128 98.0582 22.5853 97.2089 21.4998V26.9125H94.4193V12.2365H97.2089V13.5787C98.0435 12.5079 99.1345 11.9725 100.482 11.9725C101.873 11.9725 103 12.4712 103.864 13.4687C104.743 14.4515 105.182 15.8083 105.182 17.5392C105.182 19.2701 104.743 20.6343 103.864 21.6318C103 22.6293 101.873 23.128 100.482 23.128ZM99.603 20.6417C100.408 20.6417 101.053 20.3556 101.536 19.7835C102.034 19.2115 102.283 18.4634 102.283 17.5392C102.283 16.6298 102.034 15.889 101.536 15.3169C101.053 14.7449 100.408 14.4588 99.603 14.4588C99.1491 14.4588 98.6952 14.5762 98.2412 14.8109C97.7873 15.0456 97.4431 15.3316 97.2089 15.669V19.4315C97.4431 19.7689 97.7873 20.0549 98.2412 20.2896C98.7098 20.5243 99.1637 20.6417 99.603 20.6417Z" fill="#333333"/>
      <path d="M116.231 21.5218C115.206 22.5926 113.844 23.128 112.145 23.128C110.447 23.128 109.085 22.5926 108.06 21.5218C107.049 20.4363 106.544 19.1088 106.544 17.5392C106.544 15.9697 107.049 14.6495 108.06 13.5787C109.085 12.5079 110.447 11.9725 112.145 11.9725C113.844 11.9725 115.206 12.5079 116.231 13.5787C117.256 14.6495 117.768 15.9697 117.768 17.5392C117.768 19.1088 117.256 20.4363 116.231 21.5218ZM110.168 19.7615C110.652 20.3483 111.311 20.6417 112.145 20.6417C112.98 20.6417 113.639 20.3483 114.122 19.7615C114.62 19.1601 114.869 18.4194 114.869 17.5392C114.869 16.6738 114.62 15.9477 114.122 15.361C113.639 14.7595 112.98 14.4588 112.145 14.4588C111.311 14.4588 110.652 14.7595 110.168 15.361C109.685 15.9477 109.444 16.6738 109.444 17.5392C109.444 18.4194 109.685 19.1601 110.168 19.7615Z" fill="#333333"/>
      <path d="M121.222 11.0924C120.768 11.0924 120.372 10.931 120.036 10.6083C119.713 10.2709 119.552 9.87488 119.552 9.42015C119.552 8.96542 119.713 8.5767 120.036 8.25399C120.372 7.93128 120.768 7.76993 121.222 7.76993C121.69 7.76993 122.086 7.93128 122.408 8.25399C122.73 8.5767 122.891 8.96542 122.891 9.42015C122.891 9.87488 122.73 10.2709 122.408 10.6083C122.086 10.931 121.69 11.0924 121.222 11.0924ZM122.627 22.864H119.838V12.2365H122.627V22.864Z" fill="#333333"/>
      <path d="M135.344 22.864H132.554V16.4391C132.554 15.1189 131.902 14.4588 130.599 14.4588C129.589 14.4588 128.783 14.8769 128.183 15.713V22.864H125.393V12.2365H128.183V13.6227C129.106 12.5226 130.343 11.9725 131.895 11.9725C133.037 11.9725 133.894 12.2732 134.465 12.8746C135.051 13.476 135.344 14.3048 135.344 15.361V22.864Z" fill="#333333"/>
      <path d="M141.672 23.128C140.691 23.128 139.944 22.8786 139.431 22.3799C138.919 21.8812 138.663 21.1624 138.663 20.2236V14.6789H136.905V12.2365H138.663V9.33214H141.474V12.2365H143.627V14.6789H141.474V19.4755C141.474 19.8129 141.562 20.0916 141.738 20.3116C141.913 20.5316 142.148 20.6417 142.441 20.6417C142.88 20.6417 143.202 20.539 143.407 20.3336L144 22.4459C143.488 22.9006 142.711 23.128 141.672 23.128Z" fill="#333333"/>
    </svg>
  );
};

const DP_BLUE_2 = '#76a4ea';
const DP_YELLOW_CTA = '#f6ce42';
const DP_BG_WARM = '#f7f4f1';
const DP_BG_NEAR_WHITE = '#fefefe';

// Customer/× nudged -0.3px so alphabetic baseline meets logotype baseline at 0.7125×H.
const ArtifactHeader = ({ title, subtitle, customer, meta, kicker }) => (
  <header className="mb-4" style={{ fontFamily: DP_FONT_STACK }}>
    <div className="flex flex-wrap sm:flex-nowrap items-start sm:items-center justify-between gap-x-4 gap-y-2 pb-3" style={{ borderBottom: `1px solid ${DP_BORDER_SUBTLE}` }}>
      <div className="flex items-center gap-2.5 min-w-0 max-w-full">
        <div className="shrink-0 leading-none" role="img" aria-label="Drivepoint">
          <DrivepointLockup height={27} />
        </div>
        {customer ? (
          <>
            <span className="font-normal text-[15px] leading-none" style={{ color: DP_TEXT_MUTED, transform: `translateY(-0.3px)` }} aria-hidden="true">×</span>
            <span className="min-w-0 truncate font-semibold tracking-tight leading-none" style={{ color: DP_TEXT_PRIMARY, fontFamily: DP_FONT_STACK, fontSize: DP_CUSTOMER_PX, transform: `translateY(-0.3px)` }}>{customer}</span>
          </>
        ) : null}
      </div>
      {meta ? (
        <div className="w-full sm:w-auto text-[11px] font-normal text-left sm:text-right whitespace-normal sm:whitespace-nowrap shrink-0 leading-snug" style={{ color: DP_TEXT_MUTED, fontFamily: DP_FONT_STACK }}>{meta}</div>
      ) : null}
    </div>
    {kicker ? (
      <div className="text-[12px] font-semibold uppercase tracking-[0.06em] mt-8 mb-2.5" style={{ color: DP_TEXT_PRIMARY, fontFamily: DP_FONT_STACK }}>{kicker}</div>
    ) : null}
    {title ? (
      <h1 className="text-[38px] font-bold leading-tight tracking-tight m-0" style={{ color: DP_TEXT_PRIMARY, fontFamily: DP_FONT_STACK, letterSpacing: "-1px" }}>{title}</h1>
    ) : null}
    {kicker ? (
      <div aria-hidden="true" className="rounded-sm my-3.5" style={{ width: 58, height: 3, background: `linear-gradient(90deg, ${DP_BLUE_2}, ${DP_YELLOW_CTA})` }} />
    ) : null}
    {subtitle ? (
      <div className="text-base m-0" style={{ color: DP_TEXT_MUTED, fontFamily: DP_FONT_STACK }}>{subtitle}</div>
      ) : null}
    </header>
);

const ArtifactPage = ({ children, width = 920 }) => (
  <div className="min-h-full py-8 px-4" style={{ background: DP_BG_WARM }}>
    <div className="mx-auto box-border rounded-xl px-4 py-6 sm:px-8 sm:py-10 lg:px-16 lg:py-14" style={{ width, maxWidth: "100%", background: DP_BG_NEAR_WHITE, boxShadow: "0 6px 30px rgba(25, 24, 21, 0.07)" }}>
      {children}
    </div>
  </div>
);

const ArtifactSection = ({ title, children }) => (
  <section className="mt-11">
    <h2 className="text-[17px] font-bold m-0 mb-1 pb-1.5 border-b" style={{ color: DP_TEXT_PRIMARY, fontFamily: DP_FONT_STACK, borderColor: DP_BORDER_SUBTLE, letterSpacing: "-0.01em" }}>{title}</h2>
    {children}
  </section>
);

const SignatureFooter = ({ sourceLine }) => (
  <footer className="flex flex-wrap items-start sm:items-center gap-3 mt-8 pt-3" style={{ borderTop: "1px solid #ecebe9" }}>
    <div className="shrink-0 leading-none" style={{ opacity: 0.38 }} role="img" aria-label="Drivepoint">
      <DrivepointLockup height={18} />
    </div>
    <span className="min-w-0 flex-1 text-[10.5px] break-words" style={{ color: DP_TEXT_PRIMARY, opacity: 0.62, fontFamily: DP_FONT_STACK, overflowWrap: "anywhere" }}>{sourceLine}</span>
  </footer>
);

// --- Customer-built compact chrome (this connector's default) ---
// No lockup / logomark in the header. Period fills the top-right.
// Footer is the one Drivepoint brand slot.
const CompactHeader = ({ kind, period, title, subtitle }) => (
  <header className="mb-4" style={{ fontFamily: DP_FONT_STACK }}>
    <div className="flex items-baseline justify-between gap-3 pb-[11px]" style={{ borderBottom: `1px solid ${DP_BORDER_SUBTLE}` }}>
      <div className="text-[10.5px] font-bold uppercase tracking-[0.11em]" style={{ color: DP_TEXT_PRIMARY }}>{kind}</div>
      {period ? (
        <div className="text-[10.5px] font-bold uppercase tracking-[0.11em] tabular-nums shrink-0" style={{ color: DP_TEXT_MUTED }}>{period}</div>
      ) : null}
    </div>
    {title ? (
      <h1 className="text-[17px] font-bold leading-tight m-0 mt-4 mb-0.5" style={{ color: DP_TEXT_PRIMARY }}>{title}</h1>
    ) : null}
    {subtitle ? (
      <div className="text-xs m-0 mb-[18px]" style={{ color: DP_TEXT_MUTED }}>{subtitle}</div>
      ) : null}
    </header>
);

const BuiltWithFooter = ({ generated }) => (
  <footer className="flex items-center justify-between gap-3 mt-6" style={{ fontFamily: DP_FONT_STACK, fontSize: '10.5px', color: DP_TEXT_MUTED }}>
    <div className="flex items-center gap-1.5 min-w-0">
      <span className="shrink-0 leading-none opacity-70" aria-hidden="true">
        <DrivepointMark size={13} />
      </span>
      <span>Built with Drivepoint</span>
    </div>
    {generated ? <div className="shrink-0 tabular-nums">Generated {generated}</div> : null}
  </footer>
);
```

Sent-doc brand row: 1px `#ecebe9` hairline under the lockup; optional
`customer` with a `×` connector; optional `meta` on the right.

### Customer-built compact header

Default for this connector. Match the D2.1 pattern:

1. **Metadata band** — artifact type small-caps left in **ink** (`DP_TEXT_PRIMARY`,
   e.g. `MODEL UPDATE GUIDE`); period small-caps right stays **muted**
   (`DP_TEXT_MUTED`, e.g. `JULY 2026`); hairline beneath. Type leads, period
   stays quiet. **No lockup, no logomark, no client mark** in the header.
2. **Title block** — title (customer or artifact name) at 17px bold + one-line
   muted subtitle. Data is the hero; type stays restrained.
3. **Footer** — `BuiltWithFooter`: 13px mark + "Built with Drivepoint" left,
   "Generated \<date\>" muted right.

**Small-artifact collapse:** single-answer / daily-flash cards may omit the
title block and keep only the metadata band (kind + period). In that state,
`kind` names the metric or answer (for example, "Net sales"), never a generic
container such as "Single answer" or "Daily flash." Bare chrome (no header at
all) is a degradation path, not a target.

**Do not** invent client accent colors on customer-built artifacts.
Drivepoint-only: neutrals, `DP_CHART_SERIES`, and the warm status pair.

---

## Color tokens

### Brand surfaces (never a chart series hue)

- `#5b8dd8` — deep blue / logo path accent
- `#76A4EA` / `#76a4ea` — light logo path / decorative gradient accent.
  Never use it for text on a light artifact surface.
- `#f6ce42` — primary CTA / action fill (gradient bar end; not a chart series color)
- `#FFDE6A` — Drivepoint yellow (logo / accent)
- `#E1BD3D` — dark yellow (logo path)
- Neutrals: `#191815` text primary · `#716e6b` muted · `#ecebe9` hairline ·
  `#f9f8f6` / `#f7f4f1` / `#fefefe` surfaces

A chart hue never appears on a branding surface — no purple gradients, pink
accents, or cyan chrome.

### Chart series — PM-314 sequence (webapp-mui PR #469)

Discriminability palette for series 1..N. Pink, purple, cyan, and orange are
legitimate here. **Index with a modulo** — when the sequence is exhausted,
series 31 takes position 1: `DP_CHART_SERIES[i % DP_CHART_SERIES.length]`.

```js
// PM-314 / webapp-mui#469 — positions 1..30
const DP_CHART_SERIES = [
  '#3975d0', '#dca729', '#39c1d0', '#d03975', '#8436c9', '#d76c13',
  '#543ed6', '#195b5c', '#a33267', '#ca9ae9', '#4296f2', '#e1bd3d',
  '#1c2cc0', '#27a6b6', '#d98820', '#2c469e', '#e3538e', '#a354d8',
  '#515151', '#acacac', '#6fb5f6', '#e5ca59', '#2ab6c9', '#e23c7a',
  '#b472e0', '#ddb32f', '#735add', '#96caf9', '#e76ea3', '#55ccd8',
];

const DP_CHART_DELTA = {
  'forecast': '#cbd5e1',
  'negative': '#b0472f',
  'neutral': '#94a3b8',
  'positive': '#2f7d54',
};
```

Keep series color in chart marks and legend swatches. Legend label text uses
primary ink: `<Legend formatter={(value) => <span style={{ color: '#191815' }}>{value}</span>} />`.

### Semantic (deltas)

- Positive / favorable: `DP_CHART_DELTA.positive` (`#2f7d54`)
- Negative / unfavorable: `DP_CHART_DELTA.negative` (`#b0472f`)
- Neutral / zero chart mark: `DP_CHART_DELTA.neutral` (`#94a3b8`).
  Use `DP_TEXT_MUTED` for neutral numeric text so it keeps readable contrast.
- Forecast (when contrasted with actual): `DP_CHART_DELTA.forecast`
  (`#cbd5e1`) — lighter than the actual-series color; prefer reduced opacity
  or a dashed stroke when the fill alone is not enough

Never use color as the only encoder for sign or variance. Pair color with
an arrow, sign, or label.

Surface for **customer-built** shells: `bg-white` / transparent inherit.
Sent docs use `ArtifactPage` (warm `#f7f4f1` ground, near-white card).

---

## Typography

- **Use the system stack for this target.** Do not load or embed a font.
  `DP_FONT_STACK` is `ui-sans-serif, system-ui, sans-serif`, matching the
  offline artifact exception in brand-core.
- **Customer-built:** restrained type — metadata band ~10.5px small-caps
  (artifact type in ink, period muted), title 17px bold, subtitle 12px muted.
  Section labels small-caps muted. Data is the hero; do not use display-scale
  headers.
- **Sent docs:** headers `font-semibold`; `text-base` for chart titles and
  `text-xl` for dashboard headers.
- Body: same stack as headers.
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
- Ad-hoc rainbows — use `DP_CHART_SERIES` in order (PM-314), never
  invent a competing sequence

---

## Layout patterns

- **Customer-built (default for this connector):** white `p-6 bg-white`
  shell (max-width ~920). Open with
  `<CompactHeader kind={…} period={…} title={…} subtitle={…} />`.
  Close with `<BuiltWithFooter generated={…} />`. Do **not** use
  `ArtifactPage`, `ArtifactHeader`, or `SignatureFooter`. Do **not** put
  a lockup or logomark in the header. Map former `kicker` → `kind`,
  date/meta → `period`, customer or artifact name → `title`. The
  `subtitle` holds date range, plan (if SmartModel), channel filter, and
  currency — one line, separated by `·`.
- **Small-answer collapse:** single-answer / daily-flash cards may omit
  `title` / `subtitle` and keep only the metadata band (`kind` +
  `period`). When collapsed, `kind` must name the metric or answer so the
  result remains understandable without the omitted title. Bare (no chrome)
  is a degradation path, not a target.
- **Sent docs only:** wrap in `<ArtifactPage>` and pass `kicker` on
  `<ArtifactHeader title={…} subtitle={…} kicker={…} customer={…} />`
  with `SignatureFooter`. Not for connector artifacts.
- Non-data reference guides (tab-by-tab instructions, field maps):
  customer-built compact shell + Example 8 in `example-artifacts.md`.
- Dashboards: card grid for KPIs across the top (2–4 columns on desktop,
  stack on narrow), main chart below, supporting table at the bottom.
- Chart container: `<ResponsiveContainer width="100%" height={360}>`
  (≥320, ≤480 in practice). Prefer slightly tighter heights on compact
  shells when the chart is secondary to a guide body.
- Tables: sticky header (`sticky top-0 bg-white`), zebra stripes
  (`even:bg-[#f9f8f6]`), right-aligned numeric columns. Section labels
  on customer-built: small-caps muted (`text-[10.5px] font-bold
  uppercase tracking-[0.11em] text-[#716e6b]`).
- Always include a small source line when data is shown:
  `<div className="text-xs text-[#716e6b] mt-4">Source: <table names></div>`
  above `BuiltWithFooter`. Cite bare relation names (e.g.
  `ecommerce_transactions_order_level · smartmodel_actuals`) — never the
  warehouse-qualified form in customer-visible copy; that belongs in SQL only.

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
  <div className="text-xs text-[#716e6b] mt-4">
    📊 Also available in Drivepoint:{' '}
    <a
      href={REPORT_LINK.url}
      target="_blank"
      rel="noopener noreferrer"
      className="text-[#191815] underline hover:decoration-2"
    >
      {REPORT_LINK.name}
    </a>
  </div>
)}
<div className="text-xs text-[#716e6b] mt-2">
  Source: {'<table>'}
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
    <div className="bg-[#fefefe] border border-[#ecebe9] rounded shadow-sm p-3 text-sm">
      <div className="font-semibold text-[#191815] mb-1">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-[#716e6b]">{p.name}:</span>
          <span className="tabular-nums text-[#191815]">{fmtMoney(p.value, currency)}</span>
        </div>
      ))}
    </div>
  );
};
```
