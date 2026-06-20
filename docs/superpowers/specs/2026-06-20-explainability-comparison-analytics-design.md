# Design Spec: Explainability, Comparison & Analytics

**Tanggal:** 2026-06-20  
**Peneliti:** Muhammad Fauzan Saputra  
**Project:** Sistem Rekomendasi Laptop — PT Informatika Media Pratama

---

## 1. Ringkasan

Tiga fitur medium yang memperkuat nilai akademis (explainability, evaluasi) sekaligus meningkatkan UX demo ke stakeholder:

1. **Recommendation Explainability** — breakdown *mengapa* tiap laptop direkomendasikan
2. **Side-by-Side Comparison** — bandingkan 2–3 laptop dari hasil rekomendasi
3. **Analytics Dashboard** — 3 chart insight untuk admin

---

## 2. Fitur 1: Recommendation Explainability

### Tujuan
User (dan penguji sidang) dapat melihat *mengapa* laptop X muncul di Top-N — kontribusi tiap dimensi spesifikasi ke skor similarity, dan apakah spesifikasi minimum terpenuhi.

### Cara Kerja

**Engine layer (`recommender/engine.py`):**
- Tambah fungsi `explain_result(pref_raw, laptop_raw, feature_order) -> dict`
- Input: nilai raw (sebelum normalisasi) preferensi user + laptop, urutan fitur
- Output: dict `match_breakdown` — tiap fitur punya status `met` / `exceeded` / `below` dan nilai aktual vs minimum
- Status rules:
  - `met`: nilai laptop == minimum (exact match)
  - `exceeded`: nilai laptop > minimum (untuk RAM, storage, processor_tier, battery)
  - `below`: nilai laptop < minimum → tandai sebagai tidak memenuhi
  - Harga: `met` jika `budget_min ≤ harga ≤ budget_max`, `below` jika melebihi budget_max

**Service layer (`recommender/services.py`):**
- `generate_recommendation()` inject `breakdown` ke setiap entry di `results` JSON
- Struktur tiap laptop di JSON tetap backward-compatible: tambah key `breakdown` opsional

**Model (`recommender/models.py`):**
- Tidak ada perubahan schema — `results` JSON sudah fleksibel

**Template (`recommender/templates/recommender/_results.html`):**
- Tiap kartu laptop: similarity score sebagai progress bar (0–100%)
- Badge per fitur: hijau `✓ RAM 16GB` untuk met/exceeded, kuning `⚠ RAM 8GB (min: 16GB)` untuk below
- Tooltip pada badge menampilkan nilai aktual vs minimum
- Laptop dengan semua spesifikasi `met`/`exceeded` dapat border hijau ("Sangat Cocok")

### Perubahan File
- `recommender/engine.py` — fungsi `explain_result()`
- `recommender/services.py` — inject breakdown ke results
- `recommender/templates/recommender/_results.html` — render badge + progress bar
- `recommender/tests/test_engine.py` — test explain_result (met/exceeded/below/harga)

---

## 3. Fitur 2: Side-by-Side Comparison

### Tujuan
User memilih 2–3 laptop dari hasil rekomendasi dan melihat tabel perbandingan spesifikasi lengkap, dengan highlight sel terbaik per baris.

### Cara Kerja

**Frontend (`_results.html`):**
- Tiap kartu laptop punya checkbox "Bandingkan" (disabled jika sudah 3 dipilih)
- JS vanilla (< 30 baris): track array selected IDs (max 3), tampilkan/sembunyikan tombol "Bandingkan (N)"
- Tombol trigger: `hx-get="/recommend/compare/?ids=1,2,3" hx-target="#compare-section" hx-swap="innerHTML"`
- Section `#compare-section` kosong di bawah kartu hasil — diisi HTMX partial

**View (`recommender/views.py`):**
- `CompareView(LoginRequiredMixin, View)` — GET only
- Parse `ids` dari query param → split, validate integer
- **Security:** validasi setiap laptop ID ada di `Recommendation.results` milik `request.user` — cegah user akses laptop dari rekomendasi orang lain
- Ambil `Laptop` objects → render partial tabel

**Template (`recommender/templates/recommender/_compare.html`):**
- Tabel: baris = spesifikasi (RAM, Storage, Processor, GPU, Layar, Baterai, Harga), kolom = tiap laptop
- CSS class `best-value` highlight sel terbaik per baris (RAM/Storage/Baterai/Layar tertinggi, Harga terendah, Processor tier tertinggi)
- Tombol "Tutup" clear `#compare-section`

**URL (`recommender/urls.py`):**
- Tambah `path("compare/", CompareView.as_view(), name="compare")`

### Perubahan File
- `recommender/views.py` — `CompareView`
- `recommender/urls.py` — route `/recommend/compare/`
- `recommender/templates/recommender/_compare.html` — partial tabel
- `recommender/templates/recommender/_results.html` — checkbox + tombol + JS
- `recommender/tests/test_views.py` — test security validation + render

---

## 4. Fitur 3: Analytics Dashboard (Admin)

### Tujuan
Admin dapat melihat 3 chart insight pola rekomendasi — cukup untuk bahan presentasi sidang dan evaluasi sistem.

### 3 Chart

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

### Implementasi

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

### Perubahan File
- `core/plots.py` — file baru, 3 fungsi chart
- `core/views.py` — inject chart data di `DashboardView`
- `core/templates/core/dashboard.html` — section analytics

---

## 5. Error Handling & Edge Cases

| Kasus | Penanganan |
|-------|------------|
| `explain_result` fitur tidak ada di `feature_order` | Skip fitur tersebut, tidak crash |
| `CompareView` IDs tidak valid / bukan milik user | Return 400 atau redirect ke history |
| `CompareView` ID laptop tidak ditemukan di DB | Skip, render dengan laptop yang valid saja |
| Analytics chart dengan 0 data | Context = `None`, template tampilkan placeholder |
| Precision trend tanpa data 30 hari | Chart tidak dirender, bukan error |

---

## 6. Testing

### Explainability
- `test_explain_result_met` — semua spec terpenuhi → semua `met`/`exceeded`
- `test_explain_result_below` — RAM laptop < minimum → status `below`
- `test_explain_result_harga` — harga melebihi budget_max → `below`
- `test_explain_result_harga_dalam_budget` — harga dalam range → `met`

### Comparison
- `test_compare_view_valid` — 2 valid IDs milik user → 200 + tabel
- `test_compare_view_other_user_ids` — IDs dari rekomendasi user lain → 400/redirect
- `test_compare_view_no_ids` — query param kosong → 400
- `test_compare_view_max_3` — lebih dari 3 IDs → ambil 3 pertama atau 400

### Analytics
- `test_dashboard_admin_has_charts` — admin dengan data → context berisi 3 chart base64
- `test_dashboard_admin_no_data` — admin tanpa rekomendasi → context chart = None
- `test_dashboard_user_no_charts` — user biasa → tidak ada chart analytics di context

---

## 7. Urutan Implementasi

1. **Explainability** — paling tinggi nilai akademis, tidak ada dependency ke fitur lain
2. **Comparison** — bergantung pada `_results.html` yang sudah ada explainability
3. **Analytics** — independen, bisa paralel dengan comparison

---

## 8. File yang Berubah (Ringkasan)

| File | Perubahan |
|------|-----------|
| `recommender/engine.py` | Tambah `explain_result()` |
| `recommender/services.py` | Inject breakdown ke results JSON |
| `recommender/views.py` | Tambah `CompareView` |
| `recommender/urls.py` | Route `/recommend/compare/` |
| `recommender/templates/recommender/_results.html` | Badge, progress bar, checkbox, JS |
| `recommender/templates/recommender/_compare.html` | Partial tabel perbandingan (baru) |
| `recommender/tests/test_engine.py` | Test explain_result |
| `recommender/tests/test_views.py` | Test CompareView |
| `core/plots.py` | File baru, 3 fungsi chart |
| `core/views.py` | Inject analytics chart ke DashboardView |
| `core/templates/core/dashboard.html` | Section analytics 3 chart |
