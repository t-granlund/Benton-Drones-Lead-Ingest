# Benton Drones — Design System Summary

Research date: 2026-07-13  
Sources: [bentondrones.com](https://www.bentondrones.com) (homepage, about, contact, shop, product pages) + public YouTube channel [@bentondrones](https://www.youtube.com/@bentondrones).

## 1. Brand Colors

| Role | Hex | CSS variable source | Usage |
|------|-----|---------------------|-------|
| Primary / Olive Green | `#809948` | `--color-foreground: 128,152,72` | Headings, nav links, primary buttons, body text tint |
| Background / Light Gray | `#f5f5f5` | `--color-background: 245,245,245` | Page background |
| Accent / Cornflower Blue | `#6184d8` | `--color-link: 97,132,216` | Text links, secondary-button text |
| Off-white / Cream | `#fffce7` | `--gradient-background: #fffce7` (scheme-2) | Alternate section background |
| Pale Blue | `#e7ecff` | `--gradient-background: #e7ecff` (scheme-4) | Alternate section background (e.g., About page block) |
| Pale Green | `#f0f7f4` | `--gradient-background: #f0f7f4` (custom scheme) | Alternate section background |
| Pure Blue | `#0000ff` | `--gradient-background: #0000ff` (scheme-3) | Bold accent background |
| Black | `#000000` | Logo artwork | Logo, video overlay text boxes |
| White | `#ffffff` | Button text, overlays | Primary button text, video poster text |

## 2. Fonts

- **Primary typeface:** `Jost` (Google-style geometric sans-serif)
- **Font stack:** `Jost, sans-serif`
- **Body weight:** 500
- **Body bold weight:** 800
- **Heading weight:** 500
- **Body scale:** 1.3 (base ~13 px → 1.3 rem sizing)
- **Letter spacing:** 0.06 rem site-wide
- **Line height:** `calc(1 + 0.8 / var(--font-body-scale))`

All headings, body copy, navigation, and buttons use Jost. Text is set in sentence case / all-caps for navigation.

## 3. Logo Asset

- **Direct URL:** `https://www.bentondrones.com/cdn/shop/files/BENTON_DRONES_WEBSITE_LOGO.png?v=1715201940&width=500`
- **Higher-res:** append `&width=600` or use the srcset (`width=170`, `255`, `340`, `600`)
- **Description:** Black wordmark reading "BENTON DRONES" with a stylized FPV drone/propeller mark; transparent PNG, horizontal layout.

## 4. Imagery Style

- **Subject matter:** FPV drone footage, mountain biking, action sports, trail previews, scenic NWA (Northwest Arkansas) landscapes, drone operator portraits with goggles.
- **Treatment:** High-energy, cinematic action; wide/FPV chase angles; natural outdoor daylight; poster frames pulled directly from YouTube videos.
- **Color palette in imagery:** Greens, earth tones, trail dirt, blue sky, high-contrast outdoor lighting.
- **Graphics:** Simple line icons (accordion caret, checkmark) in the brand olive; minimal UI chrome.

## 5. Tone / CTA Examples

| Location | Copy | Notes |
|----------|------|-------|
| Home hero | "Drone Pilot & Videographer" / "Moving cameras to capture unique perspectives" | Short, benefit-driven |
| Services | "Extreme Sports + Action Shots", "Scenic Overhead Drone Shots", "Trail Previews", "Drone Surveys" | Direct, service-first |
| About | "Hi, I'm Anderson!" / "I started flying drones in 2020 and haven't stopped since." / "Part 107 Certified Drone Pilot + Insured" | Personal, credibility-building |
| Contact | "We'd love to hear about your project!" / "Project rates start at $1500." / "EMAIL ME - ANDERSON@BENTONDRONES.COM" | Friendly + transparent pricing |
| Newsletter | "Stay in our loop -" | Casual, inclusive |
| CTA buttons | "See my work", "Send", "Add to cart" | Action verbs, first-person on About |

## 6. Button Styling

- **Primary button:** Solid olive (`#809948`) background, white text, 1 px border, **0 px border-radius** (sharp/rectangular), no shadow.
- **Secondary / outline button:** Light background (`#f5f5f5`), cornflower-blue (`#6184d8`) text/border, 1 px border, sharp corners.
- **Button text:** Jost 500/700, sentence case.
- **Observed examples:**
  - About page: "See my work" — olive fill, white text.
  - Contact page: "Send" — olive fill, white text.
  - Product page: "Add to cart" — light fill, blue text/border.

## 7. Form Styling

- **Inputs:** Rectangular fields, **0 px border-radius**, 1 px olive-green border, no shadow.
- **Labels:** Floating / inline placeholder-style labels inside the field (e.g., "Name", "Email *", "Phone number", "Comment").
- **Layout:** 2-column for Name/Email, full-width for Phone and Comment on contact page.
- **Newsletter input:** Single email field with arrow icon submit, same sharp rectangular styling.
- **Focus states:** Not fully verified visually; theme defaults likely apply.

## 8. Inaccessible / Blocked Assets

- **Command-line fetch blocked:** `curl` returns HTTP 429 (Too Many Requests) for `bentondrones.com` pages and assets. Assets should be retrieved through a real browser session or by hot-linking the known CDN URLs.
- **Shopify theme files:** CSS/JS are served from `//www.bentondrones.com/cdn/shop/t/3/assets/…`; direct hot-linking works in browser but may be subject to Shopify CDN rate limits.

---

*See `sources.md` for source credibility and `recommendations.md` for project-specific application advice.*
