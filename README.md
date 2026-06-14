# Laptop Recommender

Sistem rekomendasi laptop berbasis web untuk membantu manajemen **PT Informatika Media Pratama**
memilih laptop secara objektif. Menggabungkan **K-Means Clustering** (jumlah cluster optimal via
Elbow Method + Silhouette Score) dengan **Content Based Filtering** (Cosine Similarity) di dalam
cluster terpilih untuk menghasilkan Top-N rekomendasi sesuai preferensi tiap peran karyawan.

Skripsi: *Implementasi Teknik Data Mining Menggunakan Content Based Filtering dengan Optimasi
K-Means Clustering pada Sistem Rekomendasi Laptop Berbasis Web di PT Informatika Media Pratama.*

## Tech Stack

- Python 3.12+ · Django 5.2 · `uv`
- PostgreSQL (psycopg + dj-database-url)
- HTMX + Tailwind (CDN, no build step)
- scikit-learn / pandas / numpy · matplotlib (plot Elbow & Silhouette)
- django-allauth (Google OAuth) · pytest + pytest-django

## Arsitektur

Lima app Django dengan engine data-mining murni (tanpa dependensi Django) agar mudah diuji:

| App | Tanggung jawab |
|-----|----------------|
| `accounts` | Profile + role (admin/user), role guard, Google OAuth |
| `catalog` | Model Laptop, CRUD admin, generator dataset dummy |
| `clustering` | `engine.py` (preprocess, Elbow, Silhouette, train), ClusterModel/Cluster, training service + dashboard |
| `recommender` | `engine.py` (pick cluster, cosine, precision@k), Preference/Recommendation, form + hasil + riwayat |
| `core` | base template, landing, dashboard |

**Invariant penting:** rekomendasi selalu memakai ulang `ClusterModel.scaler_params` + `feature_order`
dari training, sehingga vektor preferensi berada di ruang fitur yang sama dengan data laptop.

## Prasyarat

- PostgreSQL berjalan secara lokal.
- (Opsional) Kredensial Google OAuth untuk login Google.

## Setup

```bash
uv sync
cp .env.example .env          # isi nilainya
createdb laptop_recommender   # atau: createdb -O <role> laptop_recommender
uv run python manage.py migrate
uv run python manage.py generate_dummy_laptops --count 300
uv run python manage.py createsuperuser
uv run python manage.py runserver 8802
```

Buka http://localhost:8802

### Variabel `.env`

```
SECRET_KEY=...
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://USER:PASS@localhost:5432/laptop_recommender
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
ADMIN_EMAILS=email-admin@example.com     # email yang otomatis mendapat role admin saat login pertama
```

### Setup Google OAuth (manual)

1. Buat OAuth Client ID di Google Cloud Console, redirect URI:
   `http://localhost:8802/accounts/google/login/callback/`
2. Isi `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` di `.env`.
3. Di Django admin (`/admin/`), pastikan objek **Site** punya domain `localhost:8802`.

Email yang tercantum di `ADMIN_EMAILS` otomatis mendapat role **admin** saat pertama login.
Role bisa juga diubah manual lewat Django admin (model Profile).

## Alur Pemakaian

1. **Admin** menambah/kelola data laptop (menu Katalog), lalu buka **Clustering** dan klik
   *Train / Re-cluster*. Sistem menghitung K optimal (Elbow + Silhouette), menyimpan model aktif,
   menampilkan plot dan tabel interpretasi cluster.
2. **User** membuka **Rekomendasi**, mengisi preferensi (peran, budget, spesifikasi minimum),
   lalu menerima Top-5 laptop beserta cluster terpilih dan **Precision@K**.
3. **Riwayat** menyimpan setiap rekomendasi.

## Evaluasi

- **Silhouette Score** — kualitas clustering (target > 0.5 acceptable, > 0.7 good).
- **Precision@K** — relevansi rekomendasi berbasis aturan (laptop relevan jika memenuhi semua
  spesifikasi minimum + dalam budget). Target Precision@5 > 0.8.
- **UAT** — kuesioner Likert untuk manajemen (instrumen di dokumen template wawancara).

## Menjalankan Test

```bash
uv run pytest
```

## Perintah Berguna

```bash
# generate dataset dummy (reproducible)
uv run python manage.py generate_dummy_laptops --count 300 --seed 1 --clear
```
