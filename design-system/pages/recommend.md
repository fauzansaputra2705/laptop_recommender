# Page Override — Recommend & Results (`/recommend/`)

> Inherits MASTER.md. Only deviations below.

## Layout
- Two-zone: left = preference form (`lg:col-span-5`), right = `#results` target (`lg:col-span-7`). Stacks on mobile (form first, results below).
- Results zone reserves min-height with a skeleton placeholder so HTMX swap doesn't shift layout (CLS).

## Preference Form
- Grouped fieldsets with legends: **Budget** (min/max IDR), **Spesifikasi Minimum** (RAM, processor tier, storage, screen, battery), **Preferensi** (storage type, VGA type, brand, role target).
- `role_target` as a segmented control / select (developer · designer · business_analyst · manajemen).
- Budget/RAM/storage use `type="number"` (correct mobile keyboard) with `inputmode="numeric"`.
- Submit button: primary CTA "Cari Rekomendasi", full-width on mobile, `hx-post` → `#results`, `hx-indicator` spinner, disabled while loading.

## Results
- Header strip: selected cluster badge (`info` + interpretation) + **Precision@K** badge (color-coded ≥0.8 success / 0.5–0.8 warning / <0.5 danger, always with numeric value).
- Top-N as vertical stack of cards (not a dense table) — each card: brand+model (18px semibold), spec row with Lucide icons + labels, price (mono tabular), similarity badge, relevant/not-relevant badge (success+check / muted+text).
- Empty/short results: show note "Hanya X laptop di cluster ini" or "Belum ada yang memenuhi semua syarat minimum" — never a blank panel.
- No active model: `warning` alert "Admin belum melakukan training cluster" with guidance, not an error.

## Motion
- New result cards fade+translate-up, staggered 30–50ms per card. Respect reduced-motion.
