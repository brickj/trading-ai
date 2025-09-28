# Scalping Signals Atmosphere · Global Stylesheet Guidance

You asked for the rest of the experience to feel like the live `/scalping_signals` page. The refreshed `scalping-global.css` distills that look — midnight gradients, cyan gridlines, glass cards, and neon CTAs — into a single drop-in layer. Pair it with Font Awesome (for icons) and you can mock any view without rebuilding chrome.

## 1. Include These Assets

```html
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css" integrity="sha512-GL3FZmWfP7HQP9PL8uEjzsv+VKYQHzNmgP8lR+W3qIx2P2+41sJLdnOjFkWDXLI4YAlnXrhIRbkIuAeGHGZ1sA==" crossorigin="anonymous" referrerpolicy="no-referrer" />
<link rel="stylesheet" href="scalping-global.css">
```

Bootstrap is no longer required — the stylesheet ships responsive grids, cards, tables, and form treatments purpose-built for the scalping palette.

## 2. Palette, Light, and Texture

The CSS recreates the screenshot’s vibe through layered backgrounds and trace lines:

- **Backdrops**: deep charcoal gradients (`#040405` → `#0c1118`) plus subtle radial beams in cyan and violet.
- **Grid Overlay**: repeating linear gradients render the faint cyan lattice seen on the real scalping canvas.
- **Type**: Inter + Space Grotesk with wide tracking, matching the confident trading typography.
- **Accents**: Cyan (`#3df6ff`) and emerald (`#38f59d`) gradients for primary CTAs, with purple and amber for contextual tags.

## 3. Core Building Blocks

| Use case | Classes | What they mirror from `/scalping_signals` |
| --- | --- | --- |
| Page chrome | `.page`, `.nav-bar`, `.nav-brand`, `.nav-links` | Frosted nav bar with neon logo tile and underline hover effect. |
| Hero surfaces | `.hero`, `.hero-copy`, `.hero-aside`, `.glow-box` | Hover-reactive hero with cyan beams, badge ribbons, and KPI pods. |
| Calls to action | `.btn-primary`, `.btn-ghost`, `.button-row` | Cyan-to-green gradient buttons and glass-outline alternates. |
| Stats | `.metric-grid`, `.metric`, `.utility-grid`, `.stat` | KPI tiles and quick stats with mono labels and glow borders. |
| Content panels | `.panel`, `.panel-header`, `.panel-title`, `.panel-tag` | Glass cards with icon tiles, neon edge, and hover sheen. |
| Lists & tags | `.bullet-list`, `.dot`, `.tag-group`, `.tag` | Dot list and tokenized specialties in the scalping badge style. |
| Tables | `.table-wrapper`, `table`, `.status-chip` | Dense telemetry tables with cyan dividers and status pills. |
| Timelines | `.timeline`, `.timeline-item` | Vertical signal traces with halo markers for ops history. |
| Testimonials | `.testimonial` | Soft blur cards for quotes or analyst callouts. |
| Forms | `.contact-card`, `.form-grid`, `.info-line`, `input`, `select`, `textarea` | Mission-control intake with neon focus outlines and glass info rows. |

## 4. Layout System

- `.page` constrains content to ~1180px while keeping generous breathing room.
- `.section` spaces vertical bands so each module gets its own neon glow.
- `.grid-2` and `.grid-3` provide responsive splits (stacking under 720px).
- `.metric-grid` auto-fills KPI cards; `.utility-grid` handles quick stats.
- `.button-row` keeps CTAs evenly spaced and wraps on small screens.

## 5. Interaction Rules

1. Keep CTAs inside `.btn-primary` or `.btn-ghost` so the gradients match the screenshot.
2. Wrap copy-heavy blocks in `.panel` to inherit the glass sheen and hover highlight.
3. Use `.status-chip` variants (`.success`, `.warning`, `.danger`) for runbook and compliance states — they carry the neon halo effect.
4. For sequences or ops notes, `.timeline` aligns to the same cyan spine the scalping UI uses for event trails.
5. Forms sit inside `.contact-card` to maintain blur, halo borders, and consistent label tracking.

## 6. Sample Views

The `/docs/style-guide/samples` folder includes five HTML files wired to the refreshed stylesheet:

1. **Landing** — marketing hero with KPI pods and service panels that echo the screenshot’s hero.
2. **Dashboard** — telemetry stats, signal cards, timelines, and venue table styled like the live console.
3. **Market Report** — editorial layout with highlights, AI commentary, and KPI table.
4. **Team** — roster panels, avatar halos, and culture testimonials inside glass cards.
5. **Contact** — neon intake form and support touchpoints within a frosted panel.

Open them in a browser and the background, gridlines, glows, and buttons all align with the scalping reference image while covering the major AI consulting page types.
