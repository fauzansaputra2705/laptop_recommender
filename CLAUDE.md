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

## Architecture

| App | Responsibility |
|-----|----------------|
| `config` | Django settings, root URL conf, ASGI/WSGI |
| `accounts` | Profile model (admin/user role), signals, Google OAuth |
| `catalog` | Laptop, Brand, Processor, Gpu models; admin CRUD |
| `clustering` | `engine.py` (preprocess, Elbow, Silhouette, train), ClusterModel/Cluster, training service + dashboard |
| `recommender` | `engine.py` (pick cluster, cosine sim, precision@k), Preference/Recommendation, form + results + history |
| `core` | Landing page, dashboard, base template context |
| `datatable` | Reusable HTMX datatable mixin (sort, search, pagination) |

## Key Invariants

- **Scaler reuse**: Recommendation always reuses `ClusterModel.scaler_params` + `feature_order` from training — preference vector must be in same feature space as laptop data.
- **Cluster routing**: User minimum specs used for (1) relevance/Precision@K — laptop relevant if meets all minimums + in budget, (2) routing cluster + cosine — minimums floored to role target profile (`recommender/profiles.py`), price uses budget midpoint.
- **Single active model**: Only one `ClusterModel.is_active=True` at a time (enforced in `save()`).
- **Engine independence**: `clustering/engine.py` and `recommender/engine.py` have zero Django imports — pure data science, testable with plain DataFrames.

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
uv run pytest
```

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
