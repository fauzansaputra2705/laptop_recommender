# Design: Admin Analytics Dashboard + Recommendation Explainability

**Date:** 2026-06-20  
**Project:** Laptop Recommender (Skripsi — PT Informatika Media Pratama)  
**Scope:** Two independent features added to existing Django 5.2 app

---

## 1. Problem Statement

Dua gap utama pada sistem saat ini:

1. **Admin tidak punya visibility** ke performa sistem rekomendasi — tidak ada data tren, laptop populer, distribusi user, atau Precision@K agregat.
2. **User tidak mengerti kenapa** laptop tertentu direkomendasikan — hasil terasa seperti black box, mengurangi kepercayaan terhadap sistem.

---

## 2. Goals

- Admin dapat melihat analytics rekomendasi (tren, laptop populer, distribusi role, rata-rata Precision@K) tanpa keluar dari aplikasi.
- User dapat melihat radar chart yang membandingkan preferensi mereka vs spesifikasi laptop, plus checklist kriteria minimum.

---

## 3. Non-Goals

- Tidak ada real-time/WebSocket updates.
- Tidak ada export analytics ke Excel/PDF (sudah ada untuk rekomendasi history).
- Tidak ada perubahan algoritma clustering atau recommender.
- Tidak ada model baru atau migration.

---

## 4. Feature A: Admin Analytics Dashboard

### 4.1 URL & View

- URL: `/dashboard/analytics/`
- View: `AnalyticsDashboardView` di `core/views.py`
- Auth: `@staff_member_required` (admin only)
- Template: `core/templates/core/analytics.html`

### 4.2 Metrics

| Metric | Query | Visualisasi |
|--------|-------|-------------|
| Total rekomendasi all-time | `Recommendation.objects.count()` | Stat card |
| Total rekomendasi 30 hari | filter `created_at__gte` | Stat card |
| Top 5 laptop paling direkomendasikan | `values('laptop').annotate(Count).order_by('-count')[:5]` | Bar chart |
| Distribusi role user | join ke `Profile.role`, `values('role').annotate(Count)` | Pie chart |
| Tren harian (30 hari) | `TruncDay` + `annotate(Count)` | Line chart |
| Rata-rata Precision@K | `Avg('precision_at_k')` dari `Recommendation` | Stat card |

### 4.3 Charts

Gunakan **Chart.js via CDN** (bukan matplotlib) — interaktif tanpa server-side image generation, konsisten dengan pattern no-build-step.

Data dikirim sebagai JSON di template context:
```python
context['chart_data'] = {
    'top_laptops': {'labels': [...], 'values': [...]},
    'role_dist': {'labels': [...], 'values': [...]},
    'daily_trend': {'labels': [...], 'values': [...]},
}
```

Template render `<canvas>` + inline `<script>` dengan `JSON.parse`.

### 4.4 Files Changed

```
core/views.py         — tambah AnalyticsDashboardView
core/urls.py          — tambah path('dashboard/analytics/', ...)
core/templates/core/analytics.html  — baru
```

---

## 5. Feature B: Recommendation Explainability

### 5.1 Lokasi

Halaman existing: `recommender/result/<id>/` (`RecommendationDetailView`)

Tiap laptop dalam hasil rekomendasi mendapat:
1. **Radar chart** — 6 dimensi, bandingkan preferensi user vs laptop
2. **Match checklist** — kriteria minimum terpenuhi atau tidak

### 5.2 Dimensi Radar (6 axis)

| Axis | Sumber data |
|------|-------------|
| RAM | `laptop.ram_gb` vs `preference.min_ram_gb` |
| Storage | `laptop.storage_gb` vs `preference.min_storage_gb` |
| Harga | budget proximity (inverted: `1 - abs(price - budget_mid) / budget_mid`, `budget_mid = (budget_min_idr + budget_max_idr) / 2`) |
| Battery | `laptop.battery_hours` vs `preference.min_battery_hours` |
| Screen | `laptop.screen_inch` vs `preference.min_screen_inch` |
| Processor tier | `laptop.processor.tier` vs `preference.min_processor_tier` |

Semua nilai dinormalisasi ke range [0, 1] menggunakan `ClusterModel.scaler_params` (reuse dari training — konsistensi dengan engine).

### 5.3 Helper Function

Tambah di `recommender/engine.py` (zero Django imports, testable):

```python
def normalize_for_display(
    laptop: dict,
    preference: dict,
    scaler_params: dict,
    feature_order: list[str],
) -> dict[str, tuple[float, float]]:
    """
    Returns {feature_name: (laptop_normalized, preference_normalized)}
    Values clamped to [0, 1].
    """
```

### 5.4 Match Checklist

Logika boolean per kriteria:

```python
checks = {
    'RAM':     laptop.ram_gb >= preference.min_ram_gb,
    'Storage': laptop.storage_gb >= preference.min_storage_gb,
    'Harga':   laptop.price_idr <= preference.budget_max_idr,
    'VGA':     vga_match(laptop.vga.vga_type, preference.vga_type),
    'Battery': laptop.battery_hours >= preference.min_battery_hours,
}
```

Teks otomatis:
- Semua ✅ → "Semua kriteria minimum terpenuhi"
- Ada ❌ → daftar kriteria yang tidak terpenuhi

### 5.5 Data Flow

```
RecommendationDetailView.get_context_data()
  → ambil Preference + list Laptop dari Recommendation qs
  → load active ClusterModel.scaler_params + feature_order
  → for each laptop: normalize_for_display() + build checks
  → context['recommendations_display'] = [{laptop, radar_data, checks, explanation_text}]
```

Template iterasi list, render `<canvas>` per laptop dengan Chart.js radar.

### 5.6 Files Changed

```
recommender/engine.py                        — tambah normalize_for_display()
recommender/views.py                         — extend get_context_data()
recommender/templates/recommender/result.html — tambah radar section per laptop card
recommender/tests/test_views.py              — test context punya radar_data
recommender/tests/test_engine.py             — unit test normalize_for_display()
```

---

## 6. Testing Plan

| Test | File | Type |
|------|------|------|
| `normalize_for_display` returns values in [0,1] | `test_engine.py` | Unit |
| `normalize_for_display` handles edge case (price=0, scaler missing key) | `test_engine.py` | Unit |
| `RecommendationDetailView` context has `radar_data` key | `test_views.py` | View |
| `AnalyticsDashboardView` requires staff login | `core/tests/test_views.py` | View |
| `AnalyticsDashboardView` context has `chart_data` key | `core/tests/test_views.py` | View |

---

## 7. Dependencies

- **Chart.js** via CDN — tambah ke `base.html` atau block scripts per page. Tidak ada install baru.
- Tidak ada package baru di `pyproject.toml`.

---

## 8. Out of Scope (YAGNI)

- Date range picker untuk analytics
- Export analytics
- Perbandingan antar rekomendasi
- AI-generated explanation text (LLM)
- Real-time chart updates
