# Sistem Rekomendasi Laptop — Design Spec

**Judul skripsi:** Implementasi Teknik Data Mining Menggunakan Content Based Filtering dengan Optimasi K-Means Clustering pada Sistem Rekomendasi Laptop Berbasis Web di PT Informatika Media Pratama

**Tanggal:** 2026-06-14
**Peneliti:** Muhammad Fauzan Saputra (NPM 202143500586)
**Lokasi project:** `~/LATIHAN/laptop_recommender/`

---

## 1. Tujuan & Lingkup

Web app yang membantu manajemen PT Informatika Media Pratama memilih laptop secara objektif. Alur dua tahap: **K-Means Clustering** (kelompokkan dataset laptop multi-atribut, K optimal via Elbow + Silhouette) → **Content Based Filtering** dengan **Cosine Similarity** di dalam cluster terpilih untuk menghasilkan Top-N rekomendasi.

**Dalam lingkup:**
- Login Google OAuth, 2 role: Admin & User
- Admin: kelola data laptop (CRUD) + training/re-cluster + lihat plot Elbow/Silhouette
- User: input preferensi → terima Top-N rekomendasi + Precision@K
- Dataset dummy realistis (merek/spesifikasi/harga pasaran Indonesia) sebagai data awal
- Evaluasi: Silhouette Score (kualitas clustering), Precision@K (relevansi rekomendasi, rule-based)

**Di luar lingkup:** produk selain laptop, integrasi marketplace live, mobile native app.

---

## 2. Arsitektur & Stack

| Komponen | Pilihan |
|---|---|
| Bahasa | Python 3.12 |
| Package manager | `uv` |
| Web framework | Django 5.x |
| Database | PostgreSQL (psycopg + dj-database-url, config via `.env`) |
| Frontend | HTMX + FlyonUI + Tailwind (semua via CDN, no build step) |
| Data mining | scikit-learn, pandas, numpy |
| Auth | django-allauth (Google OAuth) |
| Plot | matplotlib (Elbow & Silhouette, disimpan sebagai PNG) |
| Testing | pytest + pytest-django |
| Version control | Git |

### Struktur App Django

- **`accounts`** — Google OAuth, model Profile (role admin/user), role guard (mixin/decorator)
- **`catalog`** — model Laptop, CRUD admin, management command generator dataset dummy
- **`clustering`** — K-Means engine (preprocessing, Elbow, Silhouette, train), model ClusterModel & Cluster, dashboard training
- **`recommender`** — engine rekomendasi (map cluster + Cosine Similarity + Precision@K), model Preference & Recommendation, form & hasil
- **`core`** — base template, landing, dashboard, navigasi

### Isolasi algoritma

`clustering/engine.py` dan `recommender/engine.py` adalah module Python murni (input/output numpy/pandas/dict, tidak depend ke Django ORM). Memudahkan unit test terpisah dan reasoning. View Django memanggil engine, lalu persist hasil ke DB.

---

## 3. Data Model

### Profile (`accounts`)
- `user` — OneToOne ke Django User (dari allauth)
- `role` — choice: `admin` / `user` (default `user`)
- auto-create saat first login; email admin bisa di-allowlist via `.env` (`ADMIN_EMAILS`)

### Laptop (`catalog`)
- `brand`, `model`
- `processor` (str), `processor_tier` (int ordinal, mis. i3=1…i9=8/Ryzen mapping)
- `ram_gb` (int)
- `storage_gb` (int), `storage_type` (choice: SSD/HDD)
- `vga` (str), `vga_type` (choice: integrated/dedicated)
- `screen_inch` (decimal)
- `battery_hours` (decimal)
- `price_idr` (bigint)
- `cluster_label` (int, nullable — diisi saat training)
- `created_at`, `updated_at`

### ClusterModel (`clustering`)
Snapshot satu kali training (versioned).
- `k_optimal` (int)
- `centroids` (JSON — list centroid di ruang fitur ternormalisasi)
- `silhouette_score` (float)
- `wcss_list` (JSON — WCSS per K untuk Elbow)
- `silhouette_list` (JSON — Silhouette per K)
- `scaler_params` (JSON — min/max tiap fitur numerik + mapping encoder ordinal/one-hot, dipakai ulang saat rekomendasi)
- `feature_order` (JSON — urutan kolom vektor fitur, jaga konsistensi)
- `elbow_plot` (ImageField), `silhouette_plot` (ImageField)
- `is_active` (bool — hanya satu aktif)
- `created_at`

### Cluster (`clustering`)
- `cluster_model` (FK ke ClusterModel)
- `label` (int — 0,1,2…)
- `interpretation` (str — auto: "Entry-Level"/"Mid-Range"/"High-End" dari rata-rata harga)
- `centroid` (JSON)
- `member_count` (int)
- ringkasan rata-rata atribut (JSON, untuk interpretasi)

### Preference (`recommender`)
- `user` (FK)
- `role_target` (choice: developer/designer/business_analyst/manajemen)
- `budget_min_idr`, `budget_max_idr` (bigint)
- `min_ram_gb` (int)
- `min_processor_tier` (int)
- `min_storage_gb` (int), `storage_type` (choice, nullable)
- `vga_type` (choice, nullable)
- `min_screen_inch` (decimal, nullable)
- `min_battery_hours` (decimal, nullable)
- `brand_preference` (str, nullable)
- `created_at`

### Recommendation (`recommender`)
- `user` (FK)
- `preference` (FK ke Preference)
- `cluster_model` (FK — model yang dipakai)
- `selected_cluster` (FK ke Cluster)
- `results` (JSON — list {laptop_id, nama, spesifikasi, harga, similarity})
- `precision_at_k` (float)
- `k_value` (int — N)
- `created_at`

Alur: submit form → simpan 1 Preference → jalankan engine → simpan 1 Recommendation yang merujuk Preference. History bisa dilihat ulang.

---

## 4. Data Flow

### Training (Admin)
1. Admin buka dashboard clustering → klik "Train".
2. `clustering/engine.py` ambil semua Laptop → **preprocessing**:
   - Data cleaning: tangani missing value (median/drop pada atribut kritis).
   - Outlier: **IQR clipping** (clip, bukan drop) pada numerik (harga, ram, layar, baterai).
   - Normalisasi Min-Max [0,1] untuk numerik.
   - Ordinal encoding: processor_tier, storage (kapasitas).
   - One-hot encoding: brand, vga_type.
3. Loop K=2..10 → WCSS (Elbow) + Silhouette Score per K.
4. Pilih K optimal (Silhouette tertinggi).
5. K-Means final → simpan ClusterModel baru (centroids, scaler_params, feature_order, skor, plot PNG), buat Cluster records, update `cluster_label` tiap Laptop, set `is_active=True` (nonaktifkan yang lama).
6. HTMX balikin partial: plot Elbow + Silhouette + tabel interpretasi cluster.

### Rekomendasi (User)
1. User isi form preferensi → submit (HTMX).
2. Simpan Preference → `recommender/engine.py` bangun vektor preferensi dengan **scaler_params & feature_order dari ClusterModel aktif** (vektor sejajar ruang fitur cluster).
3. Euclidean distance ke tiap centroid → pilih cluster terdekat.
4. Cosine Similarity vektor preferensi vs tiap laptop dalam cluster → sort descending → ambil Top-N.
5. Precision@K: laptop relevan jika penuhi **semua** spec minimum + dalam budget. `Precision@K = (#relevan dalam Top-K) / K`.
6. Simpan Recommendation → HTMX balikin partial: kartu Top-N + cluster terpilih + Precision@K.

**Invariant kunci:** scaler/encoder hasil training dipakai ulang saat rekomendasi. Disimpan di `ClusterModel.scaler_params` + `feature_order`.

---

## 5. Error Handling & Edge Cases

- **Train data kurang** (jumlah Laptop < ambang, mis. < 10): tolak dengan pesan jelas, tidak crash.
- **Rekomendasi tanpa ClusterModel aktif**: pesan "Admin belum melakukan training cluster".
- **Cluster terpilih kosong / Top-N < N**: tampilkan apa adanya + catatan "hanya X laptop di cluster ini".
- **Precision@K = 0**: tetap tampilkan Top-N similarity teratas + badge "tidak ada yang penuhi semua syarat minimum".
- **Outlier**: IQR clipping (bukan drop) agar laptop ekstrem tak hilang.
- **Akses role**: User buka halaman admin → 403 (mixin/decorator role tiap view).
- **OAuth / Profile**: auto-create Profile role=user saat first login; admin via allowlist `ADMIN_EMAILS` di `.env` atau Django admin.
- **Postgres down / migrasi belum jalan**: instruksi setup jelas di README.

---

## 6. Testing

pytest + pytest-django, fixture dataset dummy kecil.

- **clustering/engine**: scaling menghasilkan [0,1], encoding konsisten, Elbow/Silhouette jalan di range K, pilih K optimal sesuai skor tertinggi, centroid+label valid.
- **recommender/engine**: vektor preferensi pakai scaler training, Euclidean pilih cluster terdekat benar, Cosine Similarity urut desc, Top-N tepat, Precision@K benar (kasus semua relevan / sebagian / nol).
- **views (Django test client)**: role guard (user→403), train butuh data cukup, rekomendasi tanpa ClusterModel aktif → pesan, HTMX partial balik HTML benar.
- **models**: Profile auto-create saat login, Recommendation merujuk Preference benar.
- **dataset generator**: hasilkan N laptop realistis, spec & harga dalam range wajar.

---

## 7. Evaluasi (sesuai BAB III)

- **Silhouette Score** — kualitas clustering. Target > 0.5 (acceptable), > 0.7 (good).
- **Precision@K** — relevansi rekomendasi, rule-based otomatis. Target Precision@5 > 0.8.
- **UAT** — kuesioner Likert ke manajemen (instrumen sudah disiapkan di Template Wawancara).

---

## 8. Setup & Run

```bash
cd ~/LATIHAN/laptop_recommender
uv sync
# konfigurasi .env (DATABASE_URL, GOOGLE OAuth keys, ADMIN_EMAILS, SECRET_KEY)
uv run python manage.py migrate
uv run python manage.py generate_dummy_laptops --count 300
uv run python manage.py runserver 8802
```

URL struktur:
- `/` — landing
- `/accounts/` — allauth (Google login)
- `/dashboard/` — dashboard sesuai role
- `/catalog/` — daftar/CRUD laptop (admin)
- `/clustering/` — training & plot (admin)
- `/recommend/` — form preferensi & hasil (user)
- `/recommend/history/` — riwayat rekomendasi
