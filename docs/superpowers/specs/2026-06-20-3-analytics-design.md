# Design Spec: Analytics Dashboard (Admin)

**Tanggal:** 2026-06-20  
**Peneliti:** Muhammad Fauzan Saputra  
**Project:** Sistem Rekomendasi Laptop — PT Informatika Media Pratama

---

## Tujuan

Admin dapat melihat 3 chart insight pola rekomendasi — cukup untuk bahan presentasi sidang dan evaluasi sistem.

---

## 3 Chart

**Chart 1 — Distribusi Role Target (Donut/Pie)**
- Data: `Recommendation.objects.values('preference__role_target').annotate(count=Count('id'))`
- Visual: donut chart, tiap slice = satu role (developer/designer/business_analyst/manajemen)
- Tujuan: tampilkan role mana paling banyak menggunakan sistem

**Chart 2 — Trend Precision@K (Line)**
- Data: rata-rata `precision_at_k` per hari, 30 hari terakhir
- Query: group by `DATE(created_at)`, aggregate `Avg('precision_at_k')`
- Visual: line chart, sumbu X = tanggal, sumbu Y = precision 0–1
- Tujuan: monitor apakah kualitas rekomendasi stabil/meningkat

**Chart 3 — Distribusi Cluster Terpilih (Bar)**
- Data: `Recommendation.objects.values('selected_cluster__interpretation').annotate(count=Count('id'))`
- Visual: bar chart horizontal, label = interpretasi cluster (Entry-Level/Mid-Range/High-End)
- Tujuan: cluster mana paling sering dipilih engine

---

## Implementasi

**Plot functions (`core/plots.py` — file baru):**
- `role_distribution_png(labels, counts) -> str` — return base64 PNG
- `precision_trend_png(dates, avg_precisions) -> str` — return base64 PNG
- `cluster_usage_png(labels, counts) -> str` — return base64 PNG
- Pola sama persis dengan fungsi di `clustering/plots.py` (matplotlib → BytesIO → base64)

**View (`core/views.py` `DashboardView`):**
- Di blok `if is_admin:` — tambah query data + inject 3 chart ke context
- Hanya render chart jika ada data (`Recommendation.objects.exists()`)
- Jika belum ada data: context chart = `None`, template tampilkan placeholder

**Template (`core/templates/core/dashboard.html`):**
- Tambah section "Analitik Rekomendasi" setelah stats cards yang sudah ada
- 3 kartu chart dalam grid, masing-masing `<img src="data:image/png;base64,...">`
- Conditional: jika chart = None, tampilkan teks "Belum ada data rekomendasi"

---

## File yang Berubah

| File | Perubahan |
|------|-----------|
| `core/plots.py` | File baru, 3 fungsi chart |
| `core/views.py` | Inject analytics chart ke DashboardView |
| `core/templates/core/dashboard.html` | Section analytics 3 chart |

---

## Testing

- `test_dashboard_admin_has_charts` — admin dengan data → context berisi 3 chart base64
- `test_dashboard_admin_no_data` — admin tanpa rekomendasi → context chart = None
- `test_dashboard_user_no_charts` — user biasa → tidak ada chart analytics di context

---

## Error Handling

| Kasus | Penanganan |
|-------|------------|
| Analytics chart dengan 0 data | Context = `None`, template tampilkan placeholder |
| Precision trend tanpa data 30 hari | Chart tidak dirender, bukan error |
