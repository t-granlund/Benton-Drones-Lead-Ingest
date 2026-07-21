# Benton Drones Brand — Multi-Dimensional Analysis

## Security
- **Asset hosting:** All brand assets are served via Shopify's CDN over HTTPS. No mixed-content issues observed.
- **Privacy:** Contact/newsletter forms are standard Shopify forms; for a lead-ingest build, avoid re-posting directly to Shopify unless integrated via API.
- **CORS/rate-limit note:** Raw `curl` fetches receive HTTP 429, so any automated asset scraper needs browser-grade headers or should use the explicit CDN URLs provided.

## Cost
- **Fonts:** Jost is a free/open Google Fonts family; no licensing cost.
- **Logo:** Provided as transparent PNG; no royalty.
- **Color palette:** Simple, web-safe hex values; no premium palette dependencies.
- **Imagery:** High-quality FPV/action video exists on YouTube; reusing thumbnails or embedding videos is free, but creating original hero imagery may require drone shoots.

## Implementation Complexity
- **Low to medium.** The design system is intentionally minimal:
  - One typeface (Jost) with two weights.
  - Five core colors plus neutrals.
  - Sharp-cornered rectangular components (0 px radius) that are easy to reproduce in CSS/Tailwind/Bootstrap.
- **Shopify-specific:** The current site is Shopify-hosted; a lead-ingest app can mirror the look without needing Shopify Liquid knowledge.

## Stability
- **Theme:** Shopify "Colorblock" theme (ID 1499, v14.0.0) — mature, widely used Shopify Online Store 2.0 theme.
- **Brand assets:** Logo file is versioned (`v=1715201940`) and has been stable for over a year.
- **Color variables:** Hard-coded in inline CSS; unlikely to change without a theme re-customization.

## Optimization
- **Performance:** Shopify serves fonts and logo via global CDN with `font-display: swap`. Jost is available as a variable font or static weights; for fastest loading, self-host only the 500/700 weights.
- **Responsive:** Site uses fluid scaling (`font-body-scale: 1.3`) and breakpoints at 750 px / 990 px; follow the same pattern.
- **Accessibility:** Olive text on light gray passes for large headings but should be verified for small body copy contrast (the CSS uses `rgba(128,152,72,0.75)` for body text, which may be close to the WCAG AA line).

## Compatibility
- **Browsers:** Shopify's generated CSS targets modern browsers with fallbacks.
- **Font loading:** `font-display: swap` ensures text remains visible during load.
- **Mobile:** Navigation collapses to a drawer at < 990 px; forms stack vertically on mobile.

## Maintenance
- **Vendor lock-in:** Low for design system components; high if tied to Shopify's checkout/forms.
- **Updates:** Brand colors and fonts are stored in theme settings; for a separate lead-ingest build, hard-code the values in your own stylesheet to avoid drift.
