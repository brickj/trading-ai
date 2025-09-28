# Scalping-Inspired Global Style Recommendations

The production scalping signals experience sets the visual language we want everywhere else: deep navy atmospherics, neon glows, glass cards, and confident typography. This document captures how to translate that interface into a reusable toolkit plus five style variants you can apply across pages without losing the core identity.

## 1. Core Visual Identity
- **Color system**: Start from the scalping palette — near-black backgrounds, emerald/teal primaries, electric blue secondaries, and warm amber/pink risk cues. Every variant keeps those anchors while bending accent ratios for different moods.
- **Lighting**: Layer radial gradients behind the page shell and use translucent card fills with thin inner borders. The glow stacking in `src/web/static/css/scalping_signals.css` is mirrored through reusable variables.
- **Elevation**: Limit depth to one or two shadow intensities. Motion comes from hover lift + glow rather than heavy drop shadows, keeping parity with the live scalping grid.

## 2. Typography
- **Body**: `Inter` for legibility in data-dense layouts.
- **Headlines**: `Space Grotesk` to retain the futurist tone of the scalping header modules.
- **Eyebrows & badges**: Uppercase, high letter spacing, and subtle neon color pulls communicate precision tooling.

## 3. Layout & Spacing
- **Containers**: Wrap pages with `.page` and `.page__content` to enforce the same paddings used on the scalping view.
- **Grid helpers**: `.layout-grid--two`, `.layout-grid--three`, `.metric-grid`, and `.stat-grid` collapse gracefully on small breakpoints without breaking the rigid card rhythm.
- **Spacing scale**: Clamp-driven spacing tokens (0.25rem–4.5rem) ensure wide monitors feel expansive while laptops stay tight.

## 4. Component System
- **Cards**: `.card` surfaces blend glassmorphism, border glows, and hover sheen identical to scalping opportunity cards.
- **Stats**: `.stat-grid`, `.metric-grid`, and modifiers like `.stat--success` reuse semantic color language from the production screen.
- **Interactive pills**: `.chip`, `.tag`, `.pill`, and `.badge` echo scalping filters and metadata chips.
- **Timelines & tables**: Neon connectors, compact typography, and zebra hover states mirror scalping history panels.
- **Forms**: Inputs lean on dark chrome backgrounds with aqua focus rings so even contact workflows feel like traders’ tooling.

## 5. Motion & Accessibility
- **Transitions**: 220ms ease lifts on hover provide responsiveness without jitter.
- **Focus**: Accent-colored outlines appear on inputs/buttons to maintain keyboard usability alongside glow effects.
- **Performance**: Gradients and blurs are pure CSS (no images) to keep bundle weight small when ported into Flask templates.

## 6. File Structure
The reusable styling lives in `docs/style-guide/styles/`:
- `scalping-core.css` – shared tokens, layout primitives, and component rules extracted from the scalping page aesthetic.
- `variant-aurora.css` – bright green/teal mix for hero-driven marketing.
- `variant-circuit.css` – electric blue/violet blend tuned for dashboards.
- `variant-pulse.css` – teal/amber treatment suited for reports.
- `variant-nebula.css` – violet/neon mix for team and culture narratives.
- `variant-nocturne.css` – emerald/blue balance for contact and intake flows.

Each variant `@import`s the core file, overrides color variables, and tweaks a few context-specific patterns so you can mix-and-match while staying unmistakably “scalping”.

## 7. Sample Pages
Five static examples under `docs/style-guide/samples/` demonstrate the variants:
1. `landing.html` → Aurora palette.
2. `dashboard.html` → Circuit palette.
3. `market-report.html` → Pulse palette.
4. `team.html` → Nebula palette.
5. `contact.html` → Nocturne palette.

Open them in a browser to confirm the experience mirrors the real scalping UI while offering enough variation for different storytelling moments. Drop any template into Flask, reference the desired variant stylesheet, and you have a production-ready surface aligned with the original request.
