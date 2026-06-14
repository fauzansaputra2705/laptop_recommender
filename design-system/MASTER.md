# Design System — Laptop Recommender (MASTER)

> Global source of truth. Page-specific deviations live in `design-system/pages/<page>.md` and override this file.
> Stack: Django 5 + HTMX + FlyonUI + Tailwind (CDN). Web (desktop-first, responsive down to 375px).
> Adapted from ui-ux-pro-max rules (React Native source → web).

---

## 1. Product Profile

- **Type:** Enterprise decision-support tool (internal web app, single-tenant)
- **Audience:** Management of PT Informatika Media Pratama (admin) + general users (input preferensi)
- **Tone:** Professional, trustworthy, clean, data-first. Not playful, not flashy.
- **Density:** Comfortable. Data tables and result cards need breathing room but should fit lots of specs.

---

## 2. Visual Style

**Style:** Clean Professional Minimalism (flat, content-first).
- Flat surfaces with subtle borders + soft shadows. No skeuomorphism, no glassmorphism, no gradients on data surfaces.
- One consistent elevation scale. Cards lift slightly on hover only when interactive.
- SVG icons only (Lucide via FlyonUI). **No emoji as icons.**

**Effects tokens:**
- Radius: `rounded-lg` (8px) for cards/inputs, `rounded-md` (6px) for buttons, `rounded-full` for badges/avatars.
- Shadow: `shadow-sm` resting cards, `shadow-md` on hover/active surfaces, `shadow-lg` modals/dropdowns only.
- Border: `border border-slate-200` (light), `border-slate-700` (dark).

---

## 3. Color Tokens (semantic)

Use semantic tokens, not raw hex in templates. Map to Tailwind classes.

| Token | Light | Dark | Usage |
|---|---|---|---|
| `primary` | `indigo-600` | `indigo-400` | Primary CTA, active nav, links |
| `primary-hover` | `indigo-700` | `indigo-300` | CTA hover |
| `surface` | `white` | `slate-900` | Card / panel background |
| `surface-muted` | `slate-50` | `slate-800` | Page background, table stripes |
| `border` | `slate-200` | `slate-700` | Dividers, card borders |
| `text` | `slate-900` | `slate-100` | Body/heading text |
| `text-muted` | `slate-500` | `slate-400` | Secondary text, captions |
| `success` | `emerald-600` | `emerald-400` | Relevant badge, success toast |
| `warning` | `amber-500` | `amber-400` | "Belum training" notices |
| `danger` | `red-600` | `red-400` | Delete actions, errors |
| `info` | `sky-600` | `sky-400` | Cluster info, neutral highlights |

**Contrast rules (CRITICAL):** body text ≥ 4.5:1, large text/icons ≥ 3:1. `text-muted` only on `surface`/`surface-muted`, never muted-on-muted. Functional color always paired with icon/text (e.g. relevant = green + checkmark, not green alone).

Dark mode: desaturated tonal variants (above), not inverted. Test contrast independently.

---

## 4. Typography

**Pairing:** `Inter` (headings + body, variable) — clean, professional, excellent at small sizes for data. Optional `JetBrains Mono` for spec numbers / prices / similarity scores (tabular figures).

Load via Google Fonts with `font-display: swap`. Use `tabular-nums` (`font-variant-numeric: tabular-nums`) on price/score columns to prevent layout shift.

**Type scale (px):** 12 · 14 · 16 (base) · 18 · 20 · 24 · 30 · 36
- Body: 16px, `leading-relaxed` (1.625). Mobile body never below 16px (avoids iOS zoom).
- Captions/labels: 14px, weight 500.
- Page title: 30px bold. Section title: 20px semibold. Card title: 18px semibold.
- Line length 60–75 chars desktop; 35–60 mobile.

Weight hierarchy: headings 600–700, body 400, labels/buttons 500.

---

## 5. Layout & Spacing

- **Spacing scale:** 4 / 8 / 12 / 16 / 24 / 32 / 48 (Tailwind `1 2 3 4 6 8 12`). 8px rhythm.
- **Container:** `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8`.
- **Breakpoints:** 375 / 640 (sm) / 768 (md) / 1024 (lg) / 1280 (xl).
- **Navigation:** top app bar (sticky), `z-40`. Sidebar for admin sections on ≥1024px; collapses to top-nav menu on mobile. Active nav item highlighted (color + weight). No mixing nav patterns at same level.
- **Adaptive:** desktop-first dashboard; single-column stack on mobile, no horizontal scroll. Tables become horizontally scrollable cards or reflow on small screens.
- **z-index scale:** 0 / 10 (sticky) / 20 (dropdown) / 40 (navbar) / 50 (modal scrim) / 60 (modal).

---

## 6. Components

**Buttons:** primary (filled indigo), secondary (outline slate), danger (filled red). Min height 44px. Show spinner + disable during async (HTMX `hx-indicator`). `cursor-pointer`. One primary CTA per view.

**Forms (preference input):** visible label per field (not placeholder-only), required marked with `*`, helper text below complex fields, error below the field in `danger` + `role="alert"`. Validate on blur. Use semantic input types (`number` for budget/RAM). Group related fields (fieldset: Budget, Spesifikasi Minimum, Preferensi Merek).

**Cards (Top-N results):** title (brand + model), spec list, price (tabular-mono), similarity badge (info), relevant badge (success + check / muted "tidak penuhi syarat"). Subtle hover lift.

**Tables (catalog, history):** zebra stripes (`surface-muted`), sticky header, sortable with `aria-sort`, edit/delete actions right-aligned. Empty state with message + action.

**Charts (Elbow + Silhouette):** server-rendered matplotlib PNG with descriptive `alt` text + a short text summary of the optimal K beneath each plot (screen-reader + at-a-glance). Reserve `aspect-ratio` to avoid CLS.

**Badges:** `rounded-full` small caps. Cluster interpretation badge uses `info`; precision badge color-coded (≥0.8 success, 0.5–0.8 warning, <0.5 danger) + always show numeric value.

**Feedback:** toasts auto-dismiss 3–5s, `aria-live="polite"`, never steal focus. Confirm before delete (destructive). Skeleton/shimmer for HTMX loads > 300ms.

---

## 7. Motion

- Micro-interactions 150–300ms, `ease-out` enter / `ease-in` exit.
- Animate `transform`/`opacity` only. No animating width/height/top/left (avoid CLS).
- HTMX swaps: subtle fade-in on `#results` / `#train-output`. Respect `prefers-reduced-motion` (disable transitions).
- Max 1–2 animated elements per view. Motion conveys cause→effect, not decoration.

---

## 8. Accessibility (CRITICAL — must pass before delivery)

- Contrast 4.5:1 body / 3:1 large + icons, both themes.
- Visible focus rings (2–4px) on all interactive elements; never remove.
- Icon-only buttons get `aria-label`. Form fields use `<label for>`.
- Keyboard: tab order matches visual order; modals trap focus + Esc to close.
- Sequential headings h1→h6, no skips.
- Color never the sole signal (badges pair color + icon/text).
- Charts: `alt` + text summary; provide the cluster interpretation table as the data alternative.
- `prefers-reduced-motion` respected.

---

## 9. Anti-Patterns (avoid)

- Emoji as structural icons.
- Placeholder-only labels.
- Errors shown only at top of form (show near field).
- Gradients/heavy shadows obscuring data.
- Gray-on-gray text.
- Raw hex scattered in templates (use tokens above).
- Color-only meaning (relevant/precision must include text/icon).
- Layout shift from async content (reserve space for plots/results).
- 100vh on mobile (use `min-h-dvh`).
- More than one primary CTA per screen.

---

## 10. CDN Setup Notes

In `templates/base.html`:
- Tailwind CDN with config extending the semantic tokens above (or use Tailwind classes directly per the mapping).
- FlyonUI CSS + JS CDN (components: navbar, buttons, badges, modal, table, alerts, tabs).
- HTMX CDN. Add `htmx.org` + `hx-indicator` spinner partials.
- Google Fonts: Inter (variable) + JetBrains Mono, `display=swap`.
- `prefers-color-scheme` + a manual dark-mode toggle (FlyonUI theme), persisted in localStorage.
