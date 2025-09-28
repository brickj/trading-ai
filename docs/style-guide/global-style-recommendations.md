# Scalping Signals Global Styling Blueprint

The production `/scalping_signals` screen already nails the aesthetic the team wants across the app. Rather than inventing new tokens, the guidance below explains how to re-use that implementation everywhere else.

## 1. Source of Truth
- **Primary stylesheet**: [`src/web/static/css/styles.css`](../../src/web/static/css/styles.css) defines the near-black backdrop, neon gradients, card chrome, and typography defaults for the whole Flask app.
- **Scalping enhancements**: [`src/web/static/css/scalping_signals.css`](../../src/web/static/css/scalping_signals.css) layers on the modern card grid, summary pills, and momentum treatments seen on the live scalping page.
- **Framework dependencies**: Bootstrap 5.3 and Font Awesome 6 icons (already used by `base.html`) are required so that grid classes, buttons, and icons render correctly.

When building any new surface, load those two CSS files after Bootstrap and you will inherit the exact palette, glows, and glass cards captured in the screenshot above.

## 2. Color & Lighting
- **Background**: `styles.css` paints a radial-gradient wash over `#050505`, matching the dark trading desk atmosphere.
- **Accent colors**: Keep the scalping primaries — `#00ff88` for positive / action states, `#38c6d9` for informational tones, `#ffaa00` for momentum alerts, and `#ff4444` for risk states.
- **Glow treatment**: Cards and buttons use linear gradient overlays and subtle drop shadows (`var(--card-shadow)`) so hover states feel luminous without heavy blur filters.

## 3. Typography & Iconography
- **Font stack**: Inherit the Inter-based stack from `styles.css`; headline weights jump to 600 for confident dashboards.
- **Iconography**: Font Awesome icons provide the same semantic cues (chart line, bolt, sync) that orient users on the scalping screen. Pair icons with the neon accent colors noted above.

## 4. Layout System
- **Containers**: Wrap content in a `.container` with generous `py-5` or `mt-4` spacing, mirroring the vertical rhythm of the scalping template.
- **Cards**: Use `.card` for broader sections and `.modern-card` (from `scalping_signals.css`) when you need the tall opportunity panels with glass headers and gradient footers.
- **Data pills**: `.modern-summary-pill`, `.badge`, `.chip`, and `.tag` classes are ready-made for metric strips, status pills, and filter controls.
- **Grids**: Lean on Bootstrap’s `.row` / `.col-*` utilities, supplemented by `.g-3` gaps to achieve the tight, card-dense layout already shipping in production.

## 5. Interactions & States
- **Hover**: Buttons and cards lift ~4px and intensify glows on hover. Do not add additional transitions — reuse the `transition` rules embedded in the shared CSS.
- **Filters & toggles**: `.btn-outline-*` controls inherit the scalping outlines; combine with `.filter-btn` modifiers when porting filtering toolbars.
- **Focus**: The default focus outlines in `styles.css` meet accessibility targets while staying on-brand; avoid overriding them.

## 6. Implementation Checklist
1. Include Bootstrap + Font Awesome via CDN (see `src/web/templates/base.html`).
2. Link `styles.css`, then `scalping_signals.css` to pull in the neon trading theme.
3. Structure markup using the same component patterns (`.card`, `.modern-card`, `.modern-card-header`, summary pills) that appear on `/scalping_signals`.
4. Populate your content — the styling will automatically match the live scalping interface.

## 7. Sample Pages
Open the static samples in `docs/style-guide/samples/` to see how the production scalping aesthetic stretches across common experiences:
1. `landing.html`
2. `dashboard.html`
3. `market-report.html`
4. `team.html`
5. `contact.html`

Each file imports the exact production CSS and only swaps the markup/content, proving that the whole app can share the same look the user requested.
