# Global Style Recommendations for Trading-AI

The existing scalping signals page sets a strong baseline for a cohesive, modern interface. The recommendations below translate that look and feel into a reusable global stylesheet that can be applied across marketing, analytics, and operations surfaces.

## 1. Visual Identity
- **Color palette**: Keep the deep navy background with electric blues and teals for accents. Use warm amber and coral for warnings and risk states to provide instant semantic clarity.
- **Lighting effects**: Apply soft radial gradients on the page background and subtle glassmorphism on cards (`rgba` fills with thin light borders). This mirrors the depth seen on the scalping page without overwhelming content.
- **Elevation**: Use a single shadow token (`--shadow-soft`) for cards and buttons to maintain consistent depth.

## 2. Typography
- **Primary font**: `Inter` for body copy to maximize readability in dense dashboards.
- **Display font**: `Space Grotesk` for headings, matching the futurist tone of the scalping layout.
- **Hierarchy**: Employ `clamp()` on hero headings and maintain generous letter spacing on eyebrows/badges for a polished FinTech aesthetic.

## 3. Layout & Spacing
- **Section rhythm**: Define scale-aware spacing tokens (12px–96px). Apply them to page gutters, grid gaps, and card padding to ensure consistent breathing room.
- **Grid utilities**: Create `.layout-grid--two` and `.layout-grid--three` helpers that collapse to single column below 992px, ensuring responsive parity with existing Bootstrap layouts.
- **Page shell**: Wrap content inside `.page` and `.page__content` containers to unify padding across Flask templates and future static pages.

## 4. Reusable Components
- **Cards**: Introduce a `.card` pattern with hover lift, gradient sheen, and inner light border to replicate scalping analytics cards.
- **Badges & Pills**: Provide `.badge`, `.pill`, `.tag`, and `.chip` utilities for metadata, filters, and AI model labels.
- **Buttons**: Offer `.button` (solid) and `.button--ghost` (outline) variants with directional hover motion. These align with the dynamic CTAs on the scalping controls.
- **Stats**: Standardize `.stat-grid` and `.stat` modules for KPI clusters. Semantic modifiers (`.stat--success`, `.stat--warning`, etc.) map to the palette tokens.
- **Tables & Timelines**: Include stylings for tabular analytics and linear process visuals that extend the data-heavy voice of the product.

## 5. Micro-interactions
- **Hover feedback**: Reinforce interactivity with light translate/opacity transitions (`180ms` cubic-bezier) so controls feel responsive.
- **Dynamic glows**: Add gradient overlays on hover to emphasize actionable cards (inspired by the scalping opportunity grid).
- **Focus states**: Pair the color palette with accessible outlines to retain keyboard usability (to be added alongside JavaScript work).

## 6. Implementation Notes
- Serve the stylesheet globally through `base.html` after QA on existing Bootstrap overrides.
- Replace ad-hoc inline styles with utility classes to declutter templates.
- Consolidate duplicated color definitions currently scattered across page-specific CSS files.

## 7. Sample Pages
Five sample static pages (see `docs/style-guide/samples/`) demonstrate the recommended stylesheet in contexts spanning marketing, analytics, reporting, and engagement. They show how to reuse the same design language across:
1. A marketing/hero landing page.
2. An analytics dashboard summary.
3. A market intelligence report.
4. A leadership team page.
5. A call-to-action/contact surface.

These artifacts can be opened directly in a browser to validate visual cohesion before integrating into the Flask templates.
