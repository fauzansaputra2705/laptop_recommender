# Page Override — Clustering Dashboard (`/clustering/`) — admin only

> Inherits MASTER.md. Only deviations below. Guarded by AdminRequiredMixin (403 for users).

## Layout
- Top: status panel for the active ClusterModel (k_optimal, silhouette_score, created_at) + primary "Train / Re-cluster" button (`hx-post` → `#train-output`, `hx-indicator`).
- `#train-output` zone reserves min-height with skeleton during training (training is slow — show progress/shimmer, never a blank or frozen UI).

## Plots
- Elbow + Silhouette PNGs side by side on ≥768px, stacked on mobile.
- Each plot wrapped in a fixed `aspect-ratio` box (avoid CLS while image loads).
- Descriptive `alt` (e.g. "Elbow plot, WCSS vs K, siku di K=4") + a one-line text summary beneath ("K optimal = 4, Silhouette = 0.62").

## Cluster Interpretation Table
- This table IS the accessible data alternative to the charts — always render it.
- Columns: Label · Interpretasi (badge `info`) · Jumlah anggota · Rata-rata harga (mono tabular) · Rata-rata RAM · Rata-rata tier.
- Sortable where useful; zebra stripes.

## Feedback
- Insufficient data: `warning`/error alert echoing the message ("Butuh minimal 10 laptop untuk training") — returned as `_train_error.html` partial, not a crash.
- Success: `success` toast + refreshed status panel + plots + table in one swap.

## Motion
- Plots/table fade in on swap. Training button shows inline spinner; UI stays interactive elsewhere.
