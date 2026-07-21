# Benton Drones Brand — Project-Specific Recommendations

## Context
This research supports the **Lead-Ingest** pipeline for Benton Drones. The goal is to build branded, variant-aware lead-intake landing pages, an admin dashboard, and electronic consent/signature capture that visually match Benton Drones' existing Shopify site.

## Priority 1 — Apply the Brand Palette

Use these exact values in CSS variables or a Tailwind config:

```css
:root {
  --bd-olive: #809948;
  --bd-light-gray: #f5f5f5;
  --bd-blue: #6184d8;
  --bd-cream: #fffce7;
  --bd-pale-blue: #e7ecff;
  --bd-pale-green: #f0f7f4;
  --bd-black: #000000;
  --bd-white: #ffffff;
}
```

- Backgrounds: `--bd-light-gray` as default page background.
- Headings / primary CTAs: `--bd-olive`.
- Text links / secondary buttons: `--bd-blue`.
- Alternate section backgrounds: `--bd-pale-blue` or `--bd-pale-green` to break up long pages (matching About page block).

## Priority 2 — Use Jost Everywhere

- Set `font-family: 'Jost', sans-serif;` on `body`.
- Load only **500** (body) and **700** (headings/buttons) weights from Google Fonts or self-host the WOFF2 files from Shopify's CDN.
- Keep `letter-spacing: 0.06rem` and body scale around `1.3` (base ~13 px) to match the airy, geometric feel.

## Priority 3 — Logo & Imagery

- **Logo:** Hot-link or download `BENTON_DRONES_WEBSITE_LOGO.png` from the URL in `README.md`. Use it centered in the header, max-width ~170–255 px on desktop.
- **Imagery:** For lead-intake pages, use:
  - FPV chase stills / thumbnails from the YouTube channel (credit appropriately).
  - Outdoor NWA trail/landscape photography.
  - Avoid stock drone clichés; the brand aesthetic is raw, action-first, mountain-bike/trail-centric.

## Priority 4 — Button & Form Styling for Lead Pages

### Primary CTA (e.g., "Get a Survey Quote", "Book a Flight")
```css
.btn-primary {
  background-color: #809948;
  color: #ffffff;
  border: 1px solid #809948;
  border-radius: 0;
  padding: 1.2rem 2.4rem;
  font-family: 'Jost', sans-serif;
  font-weight: 500;
  text-transform: none;
}
```

### Secondary CTA (e.g., "View Sample Work")
```css
.btn-secondary {
  background-color: #f5f5f5;
  color: #6184d8;
  border: 1px solid #6184d8;
  border-radius: 0;
}
```

### Form Inputs
```css
input, textarea, select {
  border: 1px solid #809948;
  border-radius: 0;
  background: transparent;
  padding: 1rem;
  font-family: 'Jost', sans-serif;
}
```

- Use inline/floating labels consistent with the Shopify contact form.
- Keep consent/signature fields visually grouped with the same rectangular, sharp-cornered containers.

## Priority 5 — Tone of Voice for Copy

- **Friendly + expert:** "We'd love to hear about your project!" / "Hi, I'm Anderson!"
- **Action-oriented CTAs:** "See my work", "Send", "Book your drone survey", "Get a quote".
- **Credibility signals:** Mention "Part 107 Certified" and "Bentonville, Northwest Arkansas" where relevant.
- **Transparent pricing:** The current site states "Project rates start at $1500." Consider mirroring this clarity for drone-survey lead intake.

## Priority 6 — Accessibility & Contrast

- Verify the olive body text at 75% opacity on `#f5f5f5` meets WCAG AA for small text; if not, use full-opacity `#809948` for labels and body copy.
- Ensure interactive elements (buttons, inputs) have visible focus rings; the current Shopify theme's focus state was not fully verified.

## Priority 7 — Asset Retrieval Notes

- Because `curl` is blocked (HTTP 429), download logo/imagery through the browser or use the direct CDN URLs.
- If embedding YouTube videos, use standard YouTube embed URLs (e.g., `https://www.youtube.com/embed/vzBRyKNtSGc`) — these are public and match the brand's own homepage implementation.

## Implementation Checklist

- [ ] Add Jost font (500 + 700) to the lead-ingest app.
- [ ] Define CSS variables for the 8 brand colors.
- [ ] Create reusable `BdButton` (primary/secondary) with 0 px radius.
- [ ] Create reusable `BdInput` / `BdTextarea` with olive border and 0 px radius.
- [ ] Add centered logo header matching Shopify header layout.
- [ ] Build drone-survey landing page using the tone/CTA examples above.
- [ ] Verify contrast ratios before launch.
