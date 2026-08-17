# Architecture Page Upgrade — Findings & Recommendation (MADR-light)

**Topic:** Interactive before/after SVG comparison slider, on-diagram status badges, and "current vs next" legend for a single-file GitHub Pages page.
**Target matrix:** Safari 16+ desktop, mobile Safari 16+, WCAG 2.2 AA. Single self-contained `.html` (no build; Google Fonts + mermaid already permitted).
**Status:** Proposed · **Owner:** Solutions Architect (ID `solutions-architect-86ede2`)

> **Research-method note (transparency):** Two `web-puppy` delegations failed — one hard model error (`GLM-4.7-Flash` rejects image inputs), one returned incoherent mid-flight reasoning with no dossier on disk. Per direct-action doctrine, I verified the **decision-critical** facts myself: the WCAG 2.2 Success-Criterion levels (W3C) and the MDN `clip-path` / `inset()` documentation. The remainder is synthesized from established practice (CSS-Tricks, MDN, web.dev, W3C). Claims are tagged **(verified)** where freshly confirmed, **(synthesis)** otherwise.

---

## Context & Problem Statement

Anderson (non-technical owner) needs to grasp, in seconds on a phone, what exists today vs. what's next. The page already uses olive `#809948`, Jost, and Material-3-lite. Four questions must be answered before building: (1) the comparison-slider pattern + its Safari-safe CSS, (2) on-SVG status badges, (3) the legend/summary storytelling pattern, (4) the WCAG 2.2 accessibility traps for interactive sliders.

## Decision Drivers

Mobile touch + keyboard operability · Safari 16 / mobile-Safari 16 robustness · zero-build single-file constraint · WCAG 2.2 **AA** conformance (note which SC are actually AA vs AAA) · color-blind safety · "reads in under 5 seconds on a phone."

---

## 1. Before/After comparison slider (two inline SVGs)

### Findings — four patterns compared

| Pattern | JS? | Keyboard | Mobile touch | Safari 16 robustness | Notes |
|---|---|---|---|---|---|
| (a) `<input type="range">` -> CSS `clip-path: inset()` via a custom property | ~1 inline line (`oninput` sets `--pos`) | Yes (arrows + Home/End free) | Yes (drag + click-to-position) | Solid | **Best primary.** Native semantics = free a11y. |
| (b) Radio buttons + `:checked` + sibling `clip-path` swap | None (zero-JS) | Yes (Tab + arrows on radios) | Yes (tap a state) | Solid | **Best zero-JS fallback.** Discrete steps, not free-drag. |
| (c) `<details>` / `<summary>` accordion | None | Yes (Space/Enter) | Yes (tap) | Solid | Wrong mental model for a side-by-side reveal; good for a *list* of phases, not a slider. |
| (d) Two-button BEFORE/AFTER toggle + CSS transition | None-to-minimal (set `aria-pressed`) | Yes (Tab + Enter) | Yes (tap) | Solid | Simplest; loses the "drag to compare" affordance. |

### Recommendation

- **Primary interactive pattern -> (a) native `<input type="range">` driving `clip-path: inset()`** (synthesis; consistent with the CSS-Tricks "pure-CSS before/after" technique). Rationale: the native range input gives **drag + click-to-position + arrow-key + Home/End** for free. That triple is exactly what satisfies WCAG **2.5.7 Dragging Movements (AA, mandatory)** — a drag-only slider would *fail* AA. The reveal itself is pure CSS.
- **Zero-JS fallback -> (b) radio-button + `:checked` -> `clip-path` swap.** Truly no JavaScript; discrete before/mid/after states; fully keyboard/touch operable. Use as the no-JS baseline under progressive enhancement. (Pattern (d), the two-button toggle, is the even-simpler fallback if you prefer a binary state over steps.)

### Key CSS properties (Safari 16 / mobile-Safari 16 safest set)

- **Use `clip-path: inset(0 calc(100% - var(--pos)) 0 0)`** on the top ("after") panel. **(verified)** MDN documents `inset()`; Safari 13.1+ / iOS 13.4+, fully in 16. `inset()` is **interpolatable/animatable** and **paint-only (no layout reflow)** — the safest, smoothest reveal on mobile Safari (synthesis, per MDN formal definition).
- **Avoid `width`-based reveal** (animating `width`/`overflow:hidden` reflows layout -> jank on mobile). **Avoid CSS `mask` / `mask-image`** for the reveal (needs `-webkit-` prefix below Safari 15.4; animating masks is jankier and less predictable than `clip-path`).
- **During drag: no `transition`** on `clip-path` (instant follow = feels responsive). Apply `transition: clip-path .2s ease` **only** to the fallback toggle/radio swap.
- `will-change: clip-path` on the clipped layer — apply sparingly (only on the active slider), remove otherwise.
- `prefers-reduced-motion: reduce` -> drop the transition entirely; jump states.

### ARIA / semantics

- Keep the **native `<input type="range" min="0" max="100">`** — it exposes `role="slider"`, arrow-key operation, `aria-valuenow/min/max`, and `Home/End` natively. Add `aria-label="Reveal before and after diagram"` and a visible `<label>`. Do **not** replace it with a hand-rolled `role="slider"` div (you'd re-implement all keyboard handling and risk 2.5.7 / 2.1.1 regressions).
- Each panel as a `<figure role="img" aria-label="Before: ...">` / `"After: ..."`, **or** put `<title>` / `<desc>` inside each SVG so screen readers announce both states. The clipped "after" panel is purely visual, but its accessible name is still exposed.
- Visual divider line + handle: `aria-hidden="true"` (decorative; the range input is the control).

### Decision outcome / consequences

- **Good:** One tiny inline `oninput` line; free keyboard + 2.5.7 compliance; smooth on Safari; degrades to the radio fallback with zero JS.
- **Bad:** The "pure CSS" label is slightly misleading — a one-line inline script links the range value to `--pos` (CSS alone cannot read an input value without `:has()` hacks that are fragile on Safari). Be honest about the 1-line JS.
- **Neutral:** Discrete-step radio fallback can't free-drag — acceptable for a non-technical audience.

---

## 2. SVG annotation callouts (done / in-progress / remaining badges)

### Findings — three techniques compared

| Technique | Crisp on zoom | viewBox scaling impact | mobile Safari | Accessibility | Reflow resilience |
|---|---|---|---|---|---|
| `<foreignObject>` HTML inside SVG | Yes | Scales **with** diagram -> badge text size varies | Risk: font rendering, sizing/overflow, SVG-in-foreignObject limits (synthesis/MDN) | HTML semantics work | Medium |
| Absolute-positioned HTML pins on wrapper div | Yes | **Fixed CSS size** — consistent regardless of diagram scale | Robust | Full HTML/ARIA + Jost webfont | High |
| Native SVG `<rect>`+`<text>` (or `<symbol>`+`<use>`) | Yes (vector) | Scales with diagram | Robust | `<title>` / `role="img"`; text not selectable as HTML | High |

### Recommendation

- **Primary -> absolute-positioned HTML "pins" on a wrapper `<div>` around the SVG** (synthesis; the most robust across the mobile/desktop matrix). The SVG sits at `width:100%` with its `viewBox` so the wrapper preserves the diagram's aspect ratio; pins are positioned with **percentages** that track the responsive box. Benefit: **fixed badge size** (status badges read the same at any diagram scale), crisp, full CSS control (Jost, Material-3-lite shapes), and trivially accessible.
- **Alternative -> native SVG `<rect>` + `<text>` badges** if you specifically want badges to grow/shrink *with* the diagram (e.g., dense technical annotations). Crisp vector; expose via `<title>`.
- **Avoid `<foreignObject>` for this use case** — Safari font/overflow quirks and it scales text with the diagram (inconsistent badge size). Reserve `foreignObject` for cases where you must flow HTML *inside* SVG coordinate space.

### Key attributes (accessibility)

- Each pin: a `<button>` (if interactive) or `<span role="img" aria-label="Component X — In progress">` with a visually-hidden text node; the visible icon is `aria-hidden`.
- Diagram SVG: `role="img"` + a top-level `<title>` / `<desc>` describing the whole picture; purely decorative connector lines `aria-hidden="true"`.
- Badges carry **shape + label redundancy** (see the icon set below), never color alone (WCAG 1.4.1).
- Pin positions in `%` must be recomputed if the diagram's logical layout changes — document the coordinate map in a comment.

---

## 3. Legend + storytelling ("what exists today" vs "what's next")

### Findings — best-in-class patterns (synthesis from public docs / eng blogs)

- **AWS Architecture Center:** clean line diagrams, service icons, color-coded boxes; "current state" vs "target state" usually shown as *separate* diagrams or annotated phases, with a legend key.
- **Stripe docs:** status badges = color + short text label (Beta / GA / Deprecated); restrained typography; the **label**, not the hue, carries the meaning.
- **Vercel docs / changelog:** colored status dots + "What's New" badges; a compact summary strip up top.
- **GitHub roadmap:** status labels (Planned / In progress / Shipped) as colored chips; the *label text* is primary, color secondary.

**Common thread:** status = **(shape/icon) + label + color**, with color as the *third* signal, never the first — exactly what WCAG 1.4.1 demands.

### Recommendation — badge system (anchored on olive `#809948`)

Render the status icons as **tiny inline SVG shapes** (not unicode/emoji glyphs — emoji rendering varies across Safari and color-emoji can break contrast). Proposed set:

| State | Color | Icon (inline SVG) | Label |
|---|---|---|---|
| Done / live | olive `#809948` (filled) | checkmark | "Done" |
| In progress | amber `#C98A2B` | half-filled disc | "In progress" |
| Remaining / next | neutral gray `#6B7280` (outline) | open ring | "Remaining" |

Amber is distinct from olive in **both hue and luminance** -> color-blind safe; the inline-SVG shape is a second, independent signal; the text label is a third (WCAG 1.4.1). Verify final pairs at >= 3:1 against their backgrounds (1.4.11 Non-text Contrast).

### Recommendation — "current state at a glance" summary band

A horizontal strip pinned **above** the diagram with **3 stat chips** — each chip = colored icon + large count + label:
`[checkmark] N Done  |  [half-disc] N In progress  |  [open-ring] N Remaining`
…plus **one plain-English line** ("Current state: 12 of 20 components live; focus now on payments and reporting"). This mirrors the Vercel / GitHub summary-banner pattern and reads in under 5 seconds on a phone.

**Legend:** a tiny inline key placed directly under the band so the colors are decoded next to where they're first seen:
`checkmark = Done · half-disc = In progress · open-ring = Remaining`

### Decision outcome / consequences

- **Good:** Color-blind safe by construction (icon-first); phone-readable in one glance; olive anchors the brand; inline-SVG icons are crisp and contrast-stable.
- **Bad:** Three custom non-system colors must each be contrast-tested against both the light page background and any badge fill.
- **Neutral:** Summary band duplicates the badge counts — keep them in sync from one data source to avoid drift.

---

## 4. Accessibility checklist — WCAG 2.2 AA, slider-specific

The single most important, easy-to-miss trap for a **draggable** slider is **2.5.7 Dragging Movements — Level AA (mandatory, new in 2.2)**. A drag-only slider **fails AA**. The native range input (click + keys) is what makes you compliant. **(verified — W3C "What's New in WCAG 2.2")**

| # | SC | Level | Requirement (slider-relevant) | How we satisfy |
|---|---|---|---|---|
| 1 | **2.5.7** Dragging Movements | **AA (must)** | Draggable function also operable without dragging | Native range input: click-to-position + arrow keys |
| 2 | **2.4.11** Focus Not Obscured (Min) | **AA (must)** | Focused handle not hidden behind clipped panel | `z-index` handle above both panels; clip can't cover it |
| 3 | **2.5.8** Target Size (Min) | **AA (must)** | Hit target >= 24x24 CSS px | Enlarge the range thumb / touch area to >= 24 px (default thumbs are smaller) |
| 4 | **1.4.1** Use of Color | **AA (must)** | Don't convey state by color alone | Inline-SVG icon + text label on every badge |
| 5 | **1.4.11** Non-text Contrast | **AA (must)** | UI components / borders >= 3:1 | Focus ring, badge borders, slider track >= 3:1 |
| 6 | **2.1.1** Keyboard | **A (must)** | Fully operable without pointer | Range input + radio fallback |
| 7 | **4.1.2** Name/Role/Value | **A (must)** | Controls named / roled | `aria-label` on range; `role="img"` + `aria-label` on panels and pins |
| 8 | 2.3.3 Animation from Interactions | **AAA (should)** | Honor reduced motion | `prefers-reduced-motion` -> drop transition |
| 9 | 2.4.13 Focus Appearance | **AAA (should)** | Clear, sizable focus indicator | `:focus-visible` ring >= 2 px, 3:1 contrast |
| 10 | 1.4.3 Text Contrast | **AA (must)** | Badge label text >= 4.5:1 | Test olive / amber / gray labels vs fills |

> Note: 2.4.12, 2.4.13, and 2.3.3 are **AAA** — recommended polish, **not** required for AA conformance. 2.5.7, 2.5.8, and 2.4.11 **are** AA and **are** required.

---

## Decision summary (one line each)

1. **Slider:** native `<input type="range">` -> `clip-path: inset()` (1-line inline `oninput`); radio + `:checked` zero-JS fallback.
2. **Badges:** absolute-positioned HTML pins on a wrapper div (fixed size, crisp, accessible); avoid `foreignObject`.
3. **Legend:** olive / amber / gray badges with inline-SVG icons (checkmark / half-disc / ring) + a 3-chip "at a glance" summary band + one plain-English line.
4. **A11y:** the make-or-break SC is **2.5.7 (AA)** — never ship a drag-only slider.

## Security note (skim STRIDE)

This is a static, client-side, no-PII page — threat surface is minimal. The only real hardening: **integrity-pin the two external scripts** (Google Fonts CSS + mermaid) with **Subresource Integrity (SRI)** hashes so a compromised CDN can't inject code, and avoid inline `onclick`-style handlers beyond the unavoidable 1-line `oninput` (or move even that to `addEventListener` to keep a tight CSP). No spoofing / tampering / repudiation / information-disclosure / DoS / elevation-of-privilege concerns beyond SRI.

## References

- **W3C — What's New in WCAG 2.2** (verified live; source of the AA/AAA SC levels above): https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/
- **MDN — `clip-path`** (verified live; `inset()` documented, Safari 13.1+ / iOS 13.4+): https://developer.mozilla.org/en-US/docs/Web/CSS/clip-path
- **MDN — `<input type="range">`** (stable URL; the keyboard-operable foundation + free `role="slider"`): https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input/range
- **Named pattern (primary):** "CSS-Tricks pure-CSS before/after slider" = range input -> CSS custom property -> `clip-path: inset()`. *(CSS-Tricks' in-site search no longer surfaces the classic article post-acquisition; the technique is widely documented — mirror the MDN building blocks above.)*
- **Named pattern (fallback):** radio-button + `:checked` + sibling-selector `clip-path` swap (zero-JS).
- **Vendor storytelling references (synthesis):** AWS Architecture Center diagrams; Stripe docs status badges; Vercel "What's New" / status banners; GitHub roadmap status chips.

---
*Files created by this research: `research/architecture-page-upgrade/findings.md` (this brief). No code was generated, per request. The two attempted `web-puppy` dossiers (`research/before-after-slider/`, `research/svg-annotations-legend/`) were not written to disk — direct-action verification was used instead.*
