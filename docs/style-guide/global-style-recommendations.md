# Scalping-Inspired Global System

The production `/scalping_signals` screen already ships the neon glassmorphism aesthetic the stakeholders prefer. This document extracts the reusable rules from that page and packages them into a single global layer (`scalping-global.css`) that any static prototype or Flask template can import.

## 1. Core Files to Include

1. [Bootstrap 5.3](https://getbootstrap.com/) for the responsive grid.
2. [Font Awesome 6](https://fontawesome.com/) for iconography.
3. [`scalping-global.css`](./scalping-global.css) for the shared trading theme.

Load them in the `<head>` in the order shown so Bootstrap tokens are available before the custom scalping layer.

```html
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link rel="stylesheet" href="scalping-global.css">
```

## 2. Palette & Atmosphere

`scalping-global.css` defines a dark trading desk backdrop with neon accents lifted directly from the real scalping page:

- `--accent-green #00ff88` for primary actions and positive deltas.
- `--accent-teal #38c6d9` for informational states.
- `--accent-orange #ffaa00` for momentum or caution flags.
- `--accent-red #ff4444` for risk states.

All cards use layered gradients, soft glows, and rounded geometry identical to the live screen so the experience feels like an extension of `/scalping_signals` no matter the content.

## 3. Key Components

| Component | Classes | Notes |
| --- | --- | --- |
| Neon cards | `.neon-card`, `.neon-card__header`, `.neon-card__row` | Recreates the tall opportunity tiles with hover lift, header badges, and stat rows. |
| Glass panels | `.glass-card` | Mirrors the scalping filters/stat cards with gradient chrome and border glows. |
| Summary pills | `.summary-pill`, `.summary-pill__metric` | For hero metrics or trading desk KPIs; matches the scalping summary pill styling. |
| Chips & tags | `.neon-chip`, `.neon-chip.warning`, `.neon-chip.neutral` | Use for strategy status, asset class badges, etc. |
| Buttons | `.btn-glow`, `.btn-glow.btn-outline` | Same neon gradients and drop shadows as the “Run Analysis” CTA. |
| Tables | `.table-neon` | Styled to look like the opportunity matrix rows on the live screen. |
| Timeline | `.timeline`, `.timeline__item` | Pulls the vertical alignment and markers from the operations timeline demo. |
| Forms | `.contact-form` inputs | Pre-styled for intake flows with glowing focus states. |

## 4. Layout Helpers

- `.container` — Max width and padding tuned to the production layout.
- `.card-grid` — Responsive CSS grid for 2–3 column card decks without custom media queries.
- `.metric-grid` — 4-up stat tiles on desktop, stacked on mobile.
- `.grid-two` — Split sections that collapse on smaller breakpoints.
- Utility classes (`.flex`, `.flex-between`, `.gap-*`, `.text-success`) mirror the real scalping utility palette for quick compositions.

## 5. Usage Patterns

1. Wrap pages in `<div class="container">` to inherit the correct padding and max width.
2. Use `.hero` plus `.badge-glow` and `.hero-actions` for above-the-fold headlines that match the scalping lead.
3. Showcase KPIs inside `.summary-pill` or `.metric-grid` so numbers feel like trading telemetry.
4. Present detailed breakdowns with `.neon-card` rows or `.table-neon` tables.
5. Close pages with `.footer-cta` to reuse the neon call-to-action chrome from the scalping dashboard.

## 6. Sample Implementations

The following static HTML files demonstrate how the shared stylesheet adapts across common AI consulting flows while staying faithful to the scalping interface:

1. [`samples/landing.html`](./samples/landing.html) — Marketing splash page with hero, service grid, and KPI pill.
2. [`samples/dashboard.html`](./samples/dashboard.html) — Operations dashboard using neon cards, metrics, and task timeline.
3. [`samples/market-report.html`](./samples/market-report.html) — Research brief featuring callouts, comparison tables, and analyst insights.
4. [`samples/team.html`](./samples/team.html) — Team roster with neon talent cards and practice areas.
5. [`samples/contact.html`](./samples/contact.html) — Intake form and support info styled like the scalping intake modal.

Open them in a browser and you will see the same glow, gradients, and typography the user requested — only the content changes.
