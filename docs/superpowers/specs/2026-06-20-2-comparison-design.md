# Design Spec: Side-by-Side Comparison

**Tanggal:** 2026-06-20  
**Peneliti:** Muhammad Fauzan Saputra  
**Project:** Sistem Rekomendasi Laptop — PT Informatika Media Pratama

---

## Tujuan

User memilih 2–3 laptop dari hasil rekomendasi dan melihat tabel perbandingan spesifikasi lengkap, dengan highlight sel terbaik per baris.

---

## Cara Kerja

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

---

## File yang Berubah

| File | Perubahan |
|------|-----------|
| `recommender/views.py` | Tambah `CompareView` |
| `recommender/urls.py` | Route `/recommend/compare/` |
| `recommender/templates/recommender/_compare.html` | Partial tabel perbandingan (baru) |
| `recommender/templates/recommender/_results.html` | Checkbox + tombol + JS |
| `recommender/tests/test_views.py` | Test security validation + render |

---

## Testing

- `test_compare_view_valid` — 2 valid IDs milik user → 200 + tabel
- `test_compare_view_other_user_ids` — IDs dari rekomendasi user lain → 400/redirect
- `test_compare_view_no_ids` — query param kosong → 400
- `test_compare_view_max_3` — lebih dari 3 IDs → ambil 3 pertama atau 400

---

## Error Handling

| Kasus | Penanganan |
|-------|------------|
| IDs tidak valid / bukan milik user | Return 400 atau redirect ke history |
| ID laptop tidak ditemukan di DB | Skip, render dengan laptop yang valid saja |
