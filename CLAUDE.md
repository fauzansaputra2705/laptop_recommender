# CLAUDE.md — Laptop Recommender

## Project

Django 5.2 web app — laptop recommendation system for PT Informatika Media Pratama.
Combines K-Means Clustering (Elbow + Silhouette) with Content Based Filtering (Cosine Similarity)
to produce Top-N laptop recommendations per user role/preference.

Skripsi project. Indonesian UI, English code.

## Tech Stack

- Python 3.12+ · Django 5.2 · `uv` (package manager)
- PostgreSQL (psycopg + dj-database-url)
- HTMX + Tailwind CDN + FlyonUI (no build step)
- scikit-learn / pandas / numpy · matplotlib (Elbow & Silhouette plots)
- django-allauth (email + Google OAuth) · pytest + pytest-django
- openpyxl (Excel export) · reportlab (PDF export)

## Architecture

| App | Responsibility |
|-----|----------------|
| `config` | Django settings, root URL conf, ASGI/WSGI |
| `accounts` | Profile model (admin/user role), signals, Google OAuth |
| `catalog` | Laptop, Brand, Processor, Gpu models; admin CRUD; CSV bulk import |
| `clustering` | `engine.py` (preprocess, Elbow, Silhouette, train), `plots.py` (Elbow/Silhouette/distribution/comparison charts), ClusterModel/Cluster, training service + dashboard + evaluate |
| `recommender` | `engine.py` (pick cluster, cosine sim, precision@k, `explain_result`), `exports.py` (Excel/PDF), Preference/Recommendation, form (configurable top-N) + results (breakdown badges, similarity bar, comparison) + history + permalink |
| `core` | Landing, about, dashboard (admin analytics charts), base template context; `plots.py` (role/precision/cluster charts) |
| `datatable` | Reusable HTMX datatable mixin (sort, search, pagination) |

## Key Invariants

- **Scaler reuse**: Recommendation always reuses `ClusterModel.scaler_params` + `feature_order` from training — preference vector must be in same feature space as laptop data.
- **Cluster routing**: User minimum specs used for (1) relevance/Precision@K — laptop relevant if meets all minimums + in budget, (2) routing cluster + cosine — minimums floored to role target profile (`recommender/profiles.py`), price uses budget midpoint.
- **Single active model**: Only one `ClusterModel.is_active=True` at a time (enforced in `save()`).
- **Engine independence**: `clustering/engine.py`, `recommender/engine.py`, `recommender/exports.py`, `catalog/csv_import.py`, `core/plots.py` have zero Django imports — pure data science/IO, testable in isolation.
- **Explainability**: `explain_result(pref_raw, laptop_raw, feature_order)` returns per-feature `{status, actual, minimum}` dict — `met`/`exceeded`/`below`. Injected as `breakdown` key in each result entry by `generate_recommendation()`. Template renders color-coded badges.
- **Comparison**: `CompareView` GET `/recommend/compare/?ids=1,2,3` — validates IDs against user's own recommendations before fetching. Max 3 laptops. HTMX partial `_compare.html`.
- **Analytics charts**: `core/plots.py` generates base64 PNG — `role_distribution_png`, `precision_trend_png`, `cluster_usage_png`. Injected as `chart_role`, `chart_precision`, `chart_cluster` in admin `DashboardView`. `None` if no data.
- **Export purity**: `recommender/exports.py` builds Excel/PDF from plain `list[dict]` — no ORM. `recommendations_to_rows(qs)` is the ORM-to-dict bridge.
- **CSV import flow**: `catalog/csv_import.py` validates rows; session stores `csv_import_rows`; `ImportConfirmView` resolves FK via `get_or_create` then `bulk_create`.

## Setup

```bash
uv sync
cp .env.example .env
createdb laptop_recommender
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver 8802
```

## Commands

```bash
uv run pytest                          # 86+ tests
uv run python manage.py generate_dummy_laptops --count 300  # seed data
```

## URL Map (key routes)

| URL | View | Auth |
|-----|------|------|
| `/` | LandingView | public |
| `/about/` | AboutView | public |
| `/dashboard/` | DashboardView | login |
| `/catalog/` | LaptopListView | admin |
| `/catalog/import/` | ImportView | admin |
| `/clustering/` | DashboardView | admin |
| `/clustering/evaluate/` | EvaluateView | admin |
| `/recommend/` | RecommendView | login |
| `/recommend/result/<id>/` | RecommendationDetailView | login (own) |
| `/recommend/compare/` | CompareView | login |
| `/recommend/history/` | HistoryView | login |
| `/recommend/export/excel/` | ExportHistoryExcelView | login |
| `/recommend/export/pdf/` | ExportHistoryPdfView | login |
| `/dashboard/recommendations/export/excel/` | ExportAllRecommendationsExcelView | admin |
| `/dashboard/recommendations/export/pdf/` | ExportAllRecommendationsPdfView | admin |

## Conventions

- **Templates**: Django templates in app `templates/<app>/` dirs; global overrides in `templates/`.
- **Frontend**: Tailwind utility classes per design-system/MASTER.md tokens. HTMX for partial updates (`hx-target`, `hx-swap`). No JS build.
- **Models**: FK with `on_delete=PROTECT` for catalog entities, `CASCADE` for user data.
- **Forms**: Preference form uses role-based profiles to floor minimum specs.
- **URL patterns**: app-level `urls.py` included from `config/urls.py`.
- **Timezone**: `Asia/Jakarta`.
- **Auth**: Email-only login (`ACCOUNT_LOGIN_METHODS = {"email"}`), no email verification.

## Design System

Full spec at `design-system/MASTER.md`. TL;DR:
- Indigo primary, slate neutrals, semantic color tokens.
- Inter font + JetBrains Mono for numbers. `tabular-nums` on prices/scores.
- `rounded-lg` cards, `shadow-sm` resting, `shadow-md` hover.
- Accessibility mandatory: 4.5:1 contrast, focus rings, keyboard nav, `aria-label` on icon buttons.
