# Design Spec: Recommendation Explainability

**Tanggal:** 2026-06-20  
**Peneliti:** Muhammad Fauzan Saputra  
**Project:** Sistem Rekomendasi Laptop — PT Informatika Media Pratama

---

## Tujuan

User (dan penguji sidang) dapat melihat *mengapa* laptop X muncul di Top-N — kontribusi tiap dimensi spesifikasi ke skor similarity, dan apakah spesifikasi minimum terpenuhi.

---

## Cara Kerja

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

---

## File yang Berubah

| File | Perubahan |
|------|-----------|
| `recommender/engine.py` | Tambah `explain_result()` |
| `recommender/services.py` | Inject breakdown ke results JSON |
| `recommender/templates/recommender/_results.html` | Badge, progress bar, tooltip |
| `recommender/tests/test_engine.py` | Test explain_result |

---

## Testing

- `test_explain_result_met` — semua spec terpenuhi → semua `met`/`exceeded`
- `test_explain_result_below` — RAM laptop < minimum → status `below`
- `test_explain_result_harga` — harga melebihi budget_max → `below`
- `test_explain_result_harga_dalam_budget` — harga dalam range → `met`

---

## Error Handling

| Kasus | Penanganan |
|-------|------------|
| Fitur tidak ada di `feature_order` | Skip fitur tersebut, tidak crash |
