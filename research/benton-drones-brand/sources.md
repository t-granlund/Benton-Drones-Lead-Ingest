# Benton Drones Brand Research — Sources & Credibility

## Tier 1 (Highest)

### 1. Official Benton Drones website — live HTML/CSS
- **URL:** `https://www.bentondrones.com/`
- **Accessed:** 2026-07-13 via browser automation
- **Authority:** Primary source — the brand's own Shopify storefront.
- **Currency:** Live; footer shows © 2026, theme assets versioned `v=1715198877` etc.
- **Validation:** Cross-checked across homepage, `/pages/about`, `/pages/contact`, `/collections/all`, and a product page. All pages share the same CSS variables and logo asset.
- **Reliability:** Highest. Exact hex colors, font names, and button variables were extracted from the rendered `<style data-shopify>` block.

### 2. Official Shopify CDN logo asset
- **URL:** `https://www.bentondrones.com/cdn/shop/files/BENTON_DRONES_WEBSITE_LOGO.png?v=1715201940&width=500`
- **Authority:** Served directly from the brand's Shopify CDN.
- **Currency:** Asset timestamp `v=1715201940` (May 2024). Still in use on current site.
- **Reliability:** High — canonical logo file referenced in JSON-LD Organization markup.

## Tier 2 (High)

### 3. YouTube channel @bentondrones
- **URL:** `https://www.youtube.com/@bentondrones`
- **Accessed:** 2026-07-13
- **Authority:** Official public channel linked from the site's main navigation ("OUR WORK").
- **Currency:** Active; latest video posted ~3 weeks prior to research.
- **Validation:** Channel handle, profile icon, and video content match the brand identity and NWA location.
- **Reliability:** High for imagery style and tone examples; design system decisions on YouTube itself are platform-controlled, not brand-controlled.

## Tier 3 (Medium)

### 4. Shopify theme metadata ("Colorblock", v14.0.0)
- **Source:** Inline `<script>` on the live site.
- **Authority:** Shopify's theme store / platform.
- **Currency:** Published theme version current as of page load.
- **Reliability:** Medium-High for explaining base behavior (sharp corners, Jost font defaults), but brand-specific customizations (olive color) are the site's own settings.

## Access Limitations

- `curl` / raw HTTP fetching of `bentondrones.com` returns **HTTP 429 Too Many Requests**, indicating bot/short-burst protection. All data here was captured through a real browser rendering context.
- YouTube channel description full text was truncated behind a "...more" control that could not be expanded in this session; only the visible snippet was captured.
