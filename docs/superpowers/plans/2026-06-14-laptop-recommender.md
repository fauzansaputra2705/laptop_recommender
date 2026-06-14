# Laptop Recommender Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Django web app that recommends laptops to PT Informatika Media Pratama management using K-Means clustering (optimal K via Elbow + Silhouette) followed by Content Based Filtering with Cosine Similarity inside the selected cluster.

**Architecture:** Five Django apps (`accounts`, `catalog`, `clustering`, `recommender`, `core`). Data-mining logic lives in pure-Python engine modules (`clustering/engine.py`, `recommender/engine.py`) with no Django dependency so they can be unit-tested in isolation. Views call the engines and persist results. Training produces a versioned `ClusterModel` snapshot (centroids + scaler params) that the recommender reuses so preference vectors live in the same feature space.

**Tech Stack:** Python 3.12, `uv`, Django 5.x, PostgreSQL (psycopg + dj-database-url), HTMX + FlyonUI + Tailwind (CDN), scikit-learn / pandas / numpy, django-allauth (Google OAuth), matplotlib, pytest + pytest-django.

**Design System:** All UI tasks (T8, T12, T13, T14, T15) MUST follow `design-system/MASTER.md`. Before building a page with an override file, read it first — `design-system/pages/recommend.md` (T12), `design-system/pages/clustering.md` (T8/T15). Page rules override Master. Key non-negotiables: semantic color tokens (no raw hex), SVG icons only (no emoji), contrast ≥4.5:1 both themes, visible focus rings, labels not placeholders, 44px touch targets, reserve space for async swaps (no CLS), respect `prefers-reduced-motion`.

---

## File Structure

```
laptop_recommender/
├── manage.py
├── pyproject.toml                  # uv deps
├── .env.example                    # DATABASE_URL, GOOGLE keys, ADMIN_EMAILS, SECRET_KEY
├── config/                         # Django project package (settings, urls, wsgi, asgi)
├── accounts/                       # Google OAuth, Profile, role guard
│   ├── models.py   # Profile
│   ├── signals.py  # auto-create Profile + admin allowlist
│   ├── mixins.py   # AdminRequiredMixin, UserRequiredMixin
│   └── tests/
├── catalog/                        # Laptop CRUD + dummy generator
│   ├── models.py   # Laptop
│   ├── views.py    # list/create/update/delete (admin)
│   ├── forms.py
│   ├── management/commands/generate_dummy_laptops.py
│   └── tests/
├── clustering/                     # K-Means engine + training UI
│   ├── engine.py   # PURE python: preprocess, elbow, silhouette, train
│   ├── models.py   # ClusterModel, Cluster
│   ├── services.py # bridge engine <-> ORM, save snapshot + plots
│   ├── views.py    # dashboard, train (HTMX)
│   └── tests/
├── recommender/                    # CBF engine + recommend UI
│   ├── engine.py   # PURE python: build vector, pick cluster, cosine, precision@k
│   ├── models.py   # Preference, Recommendation
│   ├── services.py # bridge engine <-> ORM
│   ├── forms.py    # PreferenceForm
│   ├── views.py    # form, results (HTMX), history
│   └── tests/
├── core/                           # base templates, landing, dashboard
└── templates/                      # base.html (FlyonUI + HTMX CDN), partials
```

---

## Task 1: Project scaffolding with uv + Django

**Files:**
- Create: `pyproject.toml`, `manage.py`, `config/settings.py`, `.env.example`, `.gitignore`

- [ ] **Step 1: Init uv project and add deps**

```bash
cd ~/LATIHAN/laptop_recommender
uv init --python 3.12 --no-workspace
uv add "django>=5.0,<6.0" "psycopg[binary]" dj-database-url python-dotenv \
       django-allauth scikit-learn pandas numpy matplotlib pillow
uv add --dev pytest pytest-django
```
Expected: `pyproject.toml` lists all deps, `uv.lock` created.

- [ ] **Step 2: Create Django project**

Run: `uv run django-admin startproject config .`
Expected: `config/` package + `manage.py` created.

- [ ] **Step 3: Create `.env.example`**

```
SECRET_KEY=changeme-dev-secret
DEBUG=True
DATABASE_URL=postgres://postgres:postgres@localhost:5432/laptop_recommender
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
ADMIN_EMAILS=fauzan@example.com
```

- [ ] **Step 4: Wire settings.py**

In `config/settings.py`: load `.env` via python-dotenv at top; read `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` from env; set `DATABASES = {"default": dj_database_url.config(conn_max_age=600)}`; add to `INSTALLED_APPS`: `django.contrib.sites`, `allauth`, `allauth.account`, `allauth.socialaccount`, `allauth.socialaccount.providers.google`, local apps `accounts`, `catalog`, `clustering`, `recommender`, `core`; add `allauth.account.middleware.AccountMiddleware`; set `SITE_ID = 1`, allauth `AUTHENTICATION_BACKENDS`; `LOGIN_REDIRECT_URL = "/dashboard/"`; `MEDIA_URL`/`MEDIA_ROOT`. Add to `pyproject.toml` `[tool.pytest.ini_options]`: `DJANGO_SETTINGS_MODULE = "config.settings"`, `python_files = ["tests.py", "test_*.py", "*_tests.py"]`.

- [ ] **Step 5: Create `.gitignore`**

```
__pycache__/
*.pyc
.env
/media/
.venv/
```

- [ ] **Step 6: Verify project boots**

Run: `uv run python manage.py check`
Expected: `System check identified no issues`.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "chore: scaffold django project with uv, postgres, allauth deps"
```

---

## Task 2: accounts app — Profile model + role guard + Google OAuth

**Files:**
- Create: `accounts/models.py`, `accounts/signals.py`, `accounts/apps.py`, `accounts/mixins.py`, `accounts/migrations/`, `accounts/tests/test_profile.py`, `accounts/tests/__init__.py`

- [ ] **Step 1: Write failing test for Profile auto-create + admin allowlist**

`accounts/tests/test_profile.py`:
```python
import pytest
from django.contrib.auth.models import User
from accounts.models import Profile

@pytest.mark.django_db
def test_profile_created_on_user_create():
    user = User.objects.create_user("u1", email="u1@example.com", password="x")
    assert Profile.objects.filter(user=user).exists()
    assert user.profile.role == "user"

@pytest.mark.django_db
def test_admin_email_gets_admin_role(settings):
    settings.ADMIN_EMAILS = ["boss@example.com"]
    user = User.objects.create_user("boss", email="boss@example.com", password="x")
    assert user.profile.role == "admin"
```

- [ ] **Step 2: Run test, verify it fails**

Run: `uv run pytest accounts/tests/test_profile.py -v`
Expected: FAIL (`Profile` not defined / no module).

- [ ] **Step 3: Implement Profile model**

`accounts/models.py`:
```python
from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    ROLE_CHOICES = [("admin", "Admin"), ("user", "User")]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="user")

    def __str__(self):
        return f"{self.user.username} ({self.role})"

    @property
    def is_admin(self):
        return self.role == "admin"
```

- [ ] **Step 4: Implement signal**

`accounts/signals.py`:
```python
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if not created:
        return
    admin_emails = getattr(settings, "ADMIN_EMAILS", [])
    role = "admin" if instance.email and instance.email in admin_emails else "user"
    Profile.objects.create(user=instance, role=role)
```

`accounts/apps.py` — import signals in `ready()`:
```python
from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        from . import signals  # noqa: F401
```
Add `ADMIN_EMAILS = os.getenv("ADMIN_EMAILS", "").split(",")` (stripped, filtered) to settings.

- [ ] **Step 5: Make migrations, run test**

Run: `uv run python manage.py makemigrations accounts && uv run pytest accounts/tests/test_profile.py -v`
Expected: PASS.

- [ ] **Step 6: Implement role mixins**

`accounts/mixins.py`:
```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

class AdminRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.profile.is_admin:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

class UserRequiredMixin(LoginRequiredMixin):
    """Any authenticated user (admin or user) may access."""
```

- [ ] **Step 7: Configure allauth Google in settings + urls**

Add `SOCIALACCOUNT_PROVIDERS = {"google": {"APP": {"client_id": os.getenv("GOOGLE_CLIENT_ID"), "secret": os.getenv("GOOGLE_CLIENT_SECRET"), "key": ""}}}`. In `config/urls.py` add `path("accounts/", include("allauth.urls"))`. Document in README: register Google OAuth credentials and add `Site` domain via Django admin (manual setup step).

- [ ] **Step 8: Run full accounts tests + commit**

Run: `uv run pytest accounts/ -v`
Expected: PASS.
```bash
git add -A && git commit -m "feat(accounts): profile model, role guard, google oauth wiring"
```

---

## Task 3: catalog app — Laptop model

**Files:**
- Create: `catalog/models.py`, `catalog/migrations/`, `catalog/tests/test_models.py`, `catalog/tests/__init__.py`

- [ ] **Step 1: Write failing test**

`catalog/tests/test_models.py`:
```python
import pytest
from catalog.models import Laptop

@pytest.mark.django_db
def test_laptop_str_and_fields():
    lap = Laptop.objects.create(
        brand="ASUS", model="VivoBook 14", processor="Intel Core i5-1235U",
        processor_tier=5, ram_gb=16, storage_gb=512, storage_type="SSD",
        vga="Intel Iris Xe", vga_type="integrated", screen_inch=14.0,
        battery_hours=8.0, price_idr=9500000,
    )
    assert str(lap) == "ASUS VivoBook 14"
    assert lap.cluster_label is None
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest catalog/tests/test_models.py -v`
Expected: FAIL (no module `catalog.models`).

- [ ] **Step 3: Implement Laptop model**

`catalog/models.py`:
```python
from django.db import models

class Laptop(models.Model):
    STORAGE_CHOICES = [("SSD", "SSD"), ("HDD", "HDD")]
    VGA_CHOICES = [("integrated", "Integrated"), ("dedicated", "Dedicated")]

    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=120)
    processor = models.CharField(max_length=120)
    processor_tier = models.PositiveSmallIntegerField(help_text="Ordinal performance tier 1-10")
    ram_gb = models.PositiveIntegerField()
    storage_gb = models.PositiveIntegerField()
    storage_type = models.CharField(max_length=3, choices=STORAGE_CHOICES, default="SSD")
    vga = models.CharField(max_length=80)
    vga_type = models.CharField(max_length=10, choices=VGA_CHOICES, default="integrated")
    screen_inch = models.DecimalField(max_digits=4, decimal_places=1)
    battery_hours = models.DecimalField(max_digits=4, decimal_places=1)
    price_idr = models.BigIntegerField()
    cluster_label = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["brand", "model"]

    def __str__(self):
        return f"{self.brand} {self.model}"
```

- [ ] **Step 4: Migrate + run test**

Run: `uv run python manage.py makemigrations catalog && uv run pytest catalog/tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Register in admin**

`catalog/admin.py`: register `Laptop` with `list_display = ("brand","model","processor_tier","ram_gb","price_idr","cluster_label")`, `list_filter = ("brand","storage_type","vga_type")`, `search_fields = ("brand","model")`.

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat(catalog): laptop model + admin"
```

---

## Task 4: catalog — dummy dataset generator

**Files:**
- Create: `catalog/management/__init__.py`, `catalog/management/commands/__init__.py`, `catalog/management/commands/generate_dummy_laptops.py`, `catalog/tests/test_generator.py`

- [ ] **Step 1: Write failing test**

`catalog/tests/test_generator.py`:
```python
import pytest
from django.core.management import call_command
from catalog.models import Laptop

@pytest.mark.django_db
def test_generator_creates_realistic_laptops():
    call_command("generate_dummy_laptops", "--count", "50")
    assert Laptop.objects.count() == 50
    for lap in Laptop.objects.all():
        assert 1 <= lap.processor_tier <= 10
        assert lap.ram_gb in (4, 8, 16, 32, 64)
        assert 3_000_000 <= lap.price_idr <= 60_000_000
        assert 11.0 <= float(lap.screen_inch) <= 17.3
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest catalog/tests/test_generator.py -v`
Expected: FAIL (unknown command).

- [ ] **Step 3: Implement generator**

`catalog/management/commands/generate_dummy_laptops.py`: build realistic combos from fixed pools — brands `["ASUS","Lenovo","HP","Acer","Dell","MSI","Apple"]`; processor pool mapping name→tier (e.g. `("Intel Core i3-1115G4",3)`, `("Intel Core i5-1235U",5)`, `("Intel Core i7-13700H",7)`, `("Intel Core i9-13900H",9)`, `("AMD Ryzen 5 5600H",5)`, `("AMD Ryzen 7 7840HS",7)`, `("Apple M2",8)`, `("Apple M3 Pro",9)`); `ram_gb` from `[4,8,16,32,64]`; `storage_gb` from `[256,512,1024,2048]`; `vga_type` weighted (integrated more common); `screen_inch` from `[13.3,14.0,15.6,16.0,17.3]`; `battery_hours` 4–18; `price_idr` derived from a base formula scaling with `processor_tier`, `ram_gb`, dedicated VGA, plus ±10% jitter, clamped `[3_000_000, 60_000_000]`. Accept `--count` (default 300) and `--clear` (delete existing first). Use `random.seed` optional `--seed` for reproducibility. Bulk insert via `Laptop.objects.bulk_create`.

- [ ] **Step 4: Run test, verify passes**

Run: `uv run pytest catalog/tests/test_generator.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(catalog): realistic dummy laptop generator command"
```

---

## Task 5: clustering engine — preprocessing (pure Python)

**Files:**
- Create: `clustering/__init__.py` (app already exists), `clustering/engine.py`, `clustering/tests/__init__.py`, `clustering/tests/test_preprocess.py`

The engine works on plain `list[dict]` laptop records (keys match Laptop fields) so it has zero Django dependency.

- [ ] **Step 1: Write failing test for preprocessing**

`clustering/tests/test_preprocess.py`:
```python
from clustering.engine import preprocess

RECORDS = [
    {"brand":"ASUS","processor_tier":3,"ram_gb":8,"storage_gb":256,"storage_type":"SSD",
     "vga_type":"integrated","screen_inch":14.0,"battery_hours":6.0,"price_idr":7000000},
    {"brand":"MSI","processor_tier":9,"ram_gb":32,"storage_gb":1024,"storage_type":"SSD",
     "vga_type":"dedicated","screen_inch":17.3,"battery_hours":4.0,"price_idr":40000000},
    {"brand":"HP","processor_tier":5,"ram_gb":16,"storage_gb":512,"storage_type":"SSD",
     "vga_type":"integrated","screen_inch":15.6,"battery_hours":10.0,"price_idr":12000000},
]

def test_preprocess_scales_numeric_to_unit_range():
    matrix, scaler_params, feature_order = preprocess(RECORDS)
    assert len(matrix) == 3
    assert len(matrix[0]) == len(feature_order)
    # numeric columns min-max scaled into [0,1]
    for row in matrix:
        for val in row:
            assert -1e-9 <= val <= 1.0 + 1e-9
    assert "price_idr" in scaler_params["numeric"]

def test_preprocess_is_deterministic_feature_order():
    _, _, fo1 = preprocess(RECORDS)
    _, _, fo2 = preprocess(RECORDS)
    assert fo1 == fo2
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest clustering/tests/test_preprocess.py -v`
Expected: FAIL (no `preprocess`).

- [ ] **Step 3: Implement preprocess**

`clustering/engine.py`:
```python
from __future__ import annotations
import numpy as np

NUMERIC = ["processor_tier", "ram_gb", "storage_gb", "screen_inch", "battery_hours", "price_idr"]
ONEHOT = ["brand", "vga_type", "storage_type"]

def _iqr_clip(values):
    arr = np.asarray(values, dtype=float)
    q1, q3 = np.percentile(arr, [25, 75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return np.clip(arr, lo, hi)

def preprocess(records, scaler_params=None, feature_order=None):
    """Return (matrix list[list[float]], scaler_params, feature_order).
    If scaler_params/feature_order given, reuse them (for recommendation)."""
    fit = scaler_params is None
    if fit:
        scaler_params = {"numeric": {}, "categories": {}}
        # numeric: IQR clip then min-max
        clipped = {col: _iqr_clip([r[col] for r in records]) for col in NUMERIC}
        for col in NUMERIC:
            vmin, vmax = float(clipped[col].min()), float(clipped[col].max())
            scaler_params["numeric"][col] = {"min": vmin, "max": vmax}
        for col in ONEHOT:
            scaler_params["categories"][col] = sorted({str(r[col]) for r in records})

    # build feature order deterministically
    if feature_order is None:
        feature_order = list(NUMERIC)
        for col in ONEHOT:
            for cat in scaler_params["categories"][col]:
                feature_order.append(f"{col}={cat}")

    matrix = []
    for r in records:
        row = []
        for col in NUMERIC:
            p = scaler_params["numeric"][col]
            span = p["max"] - p["min"]
            v = (float(r[col]) - p["min"]) / span if span else 0.0
            row.append(min(max(v, 0.0), 1.0))
        for col in ONEHOT:
            for cat in scaler_params["categories"][col]:
                row.append(1.0 if str(r[col]) == cat else 0.0)
        matrix.append(row)
    return matrix, scaler_params, feature_order
```

- [ ] **Step 4: Run test, verify passes**

Run: `uv run pytest clustering/tests/test_preprocess.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(clustering): preprocessing engine with iqr clip + minmax + onehot"
```

---

## Task 6: clustering engine — Elbow, Silhouette, optimal K, train

**Files:**
- Modify: `clustering/engine.py`
- Create: `clustering/tests/test_train.py`

- [ ] **Step 1: Write failing test**

`clustering/tests/test_train.py`:
```python
import numpy as np
from clustering.engine import preprocess, evaluate_k_range, train

def _records(n=60):
    rng = np.random.default_rng(42)
    recs = []
    for i in range(n):
        tier = int(rng.integers(1, 11))
        recs.append({
            "brand": rng.choice(["ASUS","HP","MSI"]),
            "processor_tier": tier, "ram_gb": int(rng.choice([8,16,32])),
            "storage_gb": int(rng.choice([256,512,1024])), "storage_type": "SSD",
            "vga_type": rng.choice(["integrated","dedicated"]),
            "screen_inch": float(rng.choice([14.0,15.6,17.3])),
            "battery_hours": float(rng.integers(4,12)),
            "price_idr": int(tier * 3_000_000 + rng.integers(0, 2_000_000)),
        })
    return recs

def test_evaluate_k_range_returns_scores():
    matrix, _, _ = preprocess(_records())
    result = evaluate_k_range(matrix, k_min=2, k_max=6)
    assert list(result["k_values"]) == [2,3,4,5,6]
    assert len(result["wcss"]) == 5
    assert len(result["silhouette"]) == 5
    assert 2 <= result["k_optimal"] <= 6

def test_train_assigns_labels_and_centroids():
    matrix, _, _ = preprocess(_records())
    model = train(matrix, k=3)
    assert len(model["centroids"]) == 3
    assert len(model["labels"]) == len(matrix)
    assert set(model["labels"]).issubset({0,1,2})
    assert 0.0 <= model["silhouette_score"] <= 1.0
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest clustering/tests/test_train.py -v`
Expected: FAIL (no `evaluate_k_range`/`train`).

- [ ] **Step 3: Implement**

Append to `clustering/engine.py`:
```python
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def evaluate_k_range(matrix, k_min=2, k_max=10):
    X = np.asarray(matrix, dtype=float)
    k_max = min(k_max, len(X) - 1)
    k_values, wcss, silhouette = [], [], []
    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
        k_values.append(k)
        wcss.append(float(km.inertia_))
        silhouette.append(float(silhouette_score(X, km.labels_)))
    k_optimal = int(k_values[int(np.argmax(silhouette))])
    return {"k_values": k_values, "wcss": wcss, "silhouette": silhouette, "k_optimal": k_optimal}

def train(matrix, k):
    X = np.asarray(matrix, dtype=float)
    km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
    return {
        "k": k,
        "centroids": km.cluster_centers_.tolist(),
        "labels": km.labels_.tolist(),
        "silhouette_score": float(silhouette_score(X, km.labels_)),
        "wcss": float(km.inertia_),
    }
```

- [ ] **Step 4: Run test, verify passes**

Run: `uv run pytest clustering/tests/test_train.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(clustering): elbow, silhouette, optimal-k, train"
```

---

## Task 7: clustering models — ClusterModel + Cluster

**Files:**
- Create: `clustering/models.py`, `clustering/migrations/`, `clustering/tests/test_models.py`

- [ ] **Step 1: Write failing test**

`clustering/tests/test_models.py`:
```python
import pytest
from clustering.models import ClusterModel, Cluster

@pytest.mark.django_db
def test_only_one_active_model():
    m1 = ClusterModel.objects.create(k_optimal=3, silhouette_score=0.6,
        centroids=[], wcss_list=[], silhouette_list=[], scaler_params={},
        feature_order=[], is_active=True)
    m2 = ClusterModel.objects.create(k_optimal=4, silhouette_score=0.7,
        centroids=[], wcss_list=[], silhouette_list=[], scaler_params={},
        feature_order=[], is_active=True)
    m1.refresh_from_db()
    assert ClusterModel.objects.filter(is_active=True).count() == 1
    assert m2.is_active is True and m1.is_active is False

@pytest.mark.django_db
def test_cluster_belongs_to_model():
    m = ClusterModel.objects.create(k_optimal=2, silhouette_score=0.5,
        centroids=[], wcss_list=[], silhouette_list=[], scaler_params={},
        feature_order=[], is_active=True)
    c = Cluster.objects.create(cluster_model=m, label=0,
        interpretation="Entry-Level", centroid=[], member_count=10, summary={})
    assert c.cluster_model == m
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest clustering/tests/test_models.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement models**

`clustering/models.py`:
```python
from django.db import models

class ClusterModel(models.Model):
    k_optimal = models.PositiveSmallIntegerField()
    centroids = models.JSONField()
    silhouette_score = models.FloatField()
    wcss_list = models.JSONField()
    silhouette_list = models.JSONField()
    scaler_params = models.JSONField()
    feature_order = models.JSONField()
    elbow_plot = models.ImageField(upload_to="plots/", null=True, blank=True)
    silhouette_plot = models.ImageField(upload_to="plots/", null=True, blank=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            ClusterModel.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)

    def __str__(self):
        return f"Model #{self.pk} k={self.k_optimal} sil={self.silhouette_score:.3f}"

class Cluster(models.Model):
    cluster_model = models.ForeignKey(ClusterModel, on_delete=models.CASCADE, related_name="clusters")
    label = models.IntegerField()
    interpretation = models.CharField(max_length=40)
    centroid = models.JSONField()
    member_count = models.PositiveIntegerField()
    summary = models.JSONField(default=dict)

    class Meta:
        ordering = ["label"]

    def __str__(self):
        return f"Cluster {self.label}: {self.interpretation}"
```

- [ ] **Step 4: Migrate + run test**

Run: `uv run python manage.py makemigrations clustering && uv run pytest clustering/tests/test_models.py -v`
Expected: PASS. (`ImageField` requires Pillow, added in Task 1.)

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(clustering): ClusterModel + Cluster models with single-active invariant"
```

---

## Task 8: clustering services + training view (HTMX)

**Files:**
- Create: `clustering/services.py`, `clustering/views.py`, `clustering/urls.py`, `clustering/plots.py`, `clustering/tests/test_services.py`
- Modify: `config/urls.py`

- [ ] **Step 1: Write failing test for run_training service**

`clustering/tests/test_services.py`:
```python
import pytest
from catalog.models import Laptop
from clustering.models import ClusterModel, Cluster
from clustering.services import run_training, MIN_LAPTOPS

def _make_laptops(n):
    from django.core.management import call_command
    call_command("generate_dummy_laptops", "--count", str(n), "--seed", "1")

@pytest.mark.django_db
def test_run_training_rejects_insufficient_data():
    _make_laptops(5)
    with pytest.raises(ValueError):
        run_training()

@pytest.mark.django_db
def test_run_training_creates_active_model_and_labels():
    _make_laptops(60)
    model = run_training()
    assert model.is_active
    assert ClusterModel.objects.filter(is_active=True).count() == 1
    assert Cluster.objects.filter(cluster_model=model).count() == model.k_optimal
    # every laptop got a cluster_label
    assert Laptop.objects.filter(cluster_label__isnull=True).count() == 0
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest clustering/tests/test_services.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement plots helper**

`clustering/plots.py`: functions `elbow_png(k_values, wcss) -> ContentFile` and `silhouette_png(k_values, scores) -> ContentFile` using matplotlib `Agg` backend (`matplotlib.use("Agg")`), save to `io.BytesIO`, wrap in `django.core.files.base.ContentFile`. Label axes; mark optimal K.

- [ ] **Step 4: Implement run_training service**

`clustering/services.py`:
```python
from django.db import transaction
from catalog.models import Laptop
from clustering import engine
from clustering.models import ClusterModel, Cluster
from clustering.plots import elbow_png, silhouette_png

MIN_LAPTOPS = 10
FIELDS = ["brand","processor_tier","ram_gb","storage_gb","storage_type",
          "vga_type","screen_inch","battery_hours","price_idr"]

@transaction.atomic
def run_training():
    laptops = list(Laptop.objects.all())
    if len(laptops) < MIN_LAPTOPS:
        raise ValueError(f"Butuh minimal {MIN_LAPTOPS} laptop untuk training (ada {len(laptops)}).")
    records = [{f: getattr(l, f) for f in FIELDS} | {"_id": l.id} for l in laptops]
    matrix, scaler_params, feature_order = engine.preprocess(
        [{k: v for k, v in r.items() if k != "_id"} for r in records])
    ev = engine.evaluate_k_range(matrix, 2, 10)
    trained = engine.train(matrix, ev["k_optimal"])

    model = ClusterModel.objects.create(
        k_optimal=ev["k_optimal"], centroids=trained["centroids"],
        silhouette_score=trained["silhouette_score"], wcss_list=ev["wcss"],
        silhouette_list=ev["silhouette"], scaler_params=scaler_params,
        feature_order=feature_order, is_active=True)
    model.elbow_plot.save(f"elbow_{model.pk}.png", elbow_png(ev["k_values"], ev["wcss"]), save=False)
    model.silhouette_plot.save(f"sil_{model.pk}.png", silhouette_png(ev["k_values"], ev["silhouette"]), save=False)
    model.save()

    # assign labels + build clusters with interpretation by avg price
    labels = trained["labels"]
    by_label = {}
    for rec, lab in zip(records, labels):
        Laptop.objects.filter(pk=rec["_id"]).update(cluster_label=lab)
        by_label.setdefault(lab, []).append(rec)
    ranked = sorted(by_label.items(), key=lambda kv: sum(r["price_idr"] for r in kv[1])/len(kv[1]))
    tier_names = ["Entry-Level","Mid-Range","High-End","Premium","Workstation","Ultra"]
    label_to_name = {lab: tier_names[min(i, len(tier_names)-1)] for i,(lab,_) in enumerate(ranked)}
    for lab, recs in by_label.items():
        avg = lambda key: sum(r[key] for r in recs)/len(recs)
        Cluster.objects.create(
            cluster_model=model, label=lab, interpretation=label_to_name[lab],
            centroid=trained["centroids"][lab], member_count=len(recs),
            summary={"avg_price": avg("price_idr"), "avg_ram": avg("ram_gb"),
                     "avg_tier": avg("processor_tier")})
    return model
```

- [ ] **Step 5: Run test, verify passes**

Run: `uv run pytest clustering/tests/test_services.py -v`
Expected: PASS.

- [ ] **Step 6: Implement views + urls (HTMX)**

`clustering/views.py`: `DashboardView(AdminRequiredMixin, TemplateView)` renders active model + clusters + plots. `train_view(request)` (POST, admin-only) calls `run_training()`, catches `ValueError` → returns partial `clustering/_train_error.html`, on success returns partial `clustering/_train_result.html` (plots + cluster table). `config/urls.py`: `path("clustering/", include("clustering.urls"))` with names `clustering:dashboard`, `clustering:train`.

- [ ] **Step 7: Run full clustering tests + commit**

Run: `uv run pytest clustering/ -v`
Expected: PASS.
```bash
git add -A && git commit -m "feat(clustering): training service, plots, htmx dashboard"
```

---

## Task 9: recommender engine — vector, cluster pick, cosine, precision@k (pure Python)

**Files:**
- Create: `recommender/engine.py`, `recommender/tests/__init__.py`, `recommender/tests/test_engine.py`

The engine reuses `clustering.engine.preprocess` with saved `scaler_params`/`feature_order` so the preference vector lives in the training feature space.

- [ ] **Step 1: Write failing test**

`recommender/tests/test_engine.py`:
```python
import numpy as np
from recommender.engine import pick_cluster, cosine_topn, precision_at_k

def test_pick_cluster_returns_nearest_centroid():
    centroids = [[0.0, 0.0], [1.0, 1.0]]
    assert pick_cluster([0.1, 0.1], centroids) == 0
    assert pick_cluster([0.9, 0.8], centroids) == 1

def test_cosine_topn_orders_descending():
    pref = [1.0, 0.0]
    laptops = [
        {"id": 1, "vector": [1.0, 0.0]},   # sim 1.0
        {"id": 2, "vector": [0.0, 1.0]},   # sim 0.0
        {"id": 3, "vector": [0.7, 0.7]},   # sim ~0.7
    ]
    top = cosine_topn(pref, laptops, n=2)
    assert [t["id"] for t in top] == [1, 3]
    assert top[0]["similarity"] >= top[1]["similarity"]

def test_precision_at_k():
    results = [{"relevant": True}, {"relevant": True}, {"relevant": False},
               {"relevant": True}, {"relevant": False}]
    assert precision_at_k(results, k=5) == 0.6
    assert precision_at_k(results, k=2) == 1.0
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest recommender/tests/test_engine.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement engine**

`recommender/engine.py`:
```python
from __future__ import annotations
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def pick_cluster(pref_vector, centroids):
    pv = np.asarray(pref_vector, dtype=float)
    dists = [np.linalg.norm(pv - np.asarray(c, dtype=float)) for c in centroids]
    return int(np.argmin(dists))

def cosine_topn(pref_vector, laptops, n=5):
    """laptops: list of dicts with 'vector'. Returns top-n copies with 'similarity'."""
    if not laptops:
        return []
    vectors = [lap["vector"] for lap in laptops]
    sims = cosine_similarity([pref_vector], vectors)[0]
    ranked = sorted(
        ({**lap, "similarity": float(s)} for lap, s in zip(laptops, sims)),
        key=lambda d: d["similarity"], reverse=True,
    )
    return ranked[:n]

def precision_at_k(results, k):
    top = results[:k]
    if not top:
        return 0.0
    relevant = sum(1 for r in top if r.get("relevant"))
    return relevant / len(top)

def is_relevant(laptop, pref):
    """Rule: laptop relevant if it meets all minimum specs + within budget."""
    if pref.get("budget_max_idr") and laptop["price_idr"] > pref["budget_max_idr"]:
        return False
    if pref.get("budget_min_idr") and laptop["price_idr"] < pref["budget_min_idr"]:
        return False
    checks = [
        ("min_ram_gb", "ram_gb"), ("min_processor_tier", "processor_tier"),
        ("min_storage_gb", "storage_gb"), ("min_screen_inch", "screen_inch"),
        ("min_battery_hours", "battery_hours"),
    ]
    for pref_key, lap_key in checks:
        if pref.get(pref_key) and laptop[lap_key] < pref[pref_key]:
            return False
    if pref.get("storage_type") and laptop["storage_type"] != pref["storage_type"]:
        return False
    if pref.get("vga_type") and laptop["vga_type"] != pref["vga_type"]:
        return False
    if pref.get("brand_preference") and laptop["brand"] != pref["brand_preference"]:
        return False
    return True
```

- [ ] **Step 4: Run test, verify passes**

Run: `uv run pytest recommender/tests/test_engine.py -v`
Expected: PASS.

- [ ] **Step 5: Add relevance test + commit**

Add a `test_is_relevant` case (laptop within budget & meeting specs → True; one failing spec → False) and run it.
```bash
git add -A && git commit -m "feat(recommender): cosine topn, cluster pick, precision@k, relevance rule"
```

---

## Task 10: recommender models — Preference + Recommendation

**Files:**
- Create: `recommender/models.py`, `recommender/migrations/`, `recommender/tests/test_models.py`

- [ ] **Step 1: Write failing test**

`recommender/tests/test_models.py`:
```python
import pytest
from django.contrib.auth.models import User
from clustering.models import ClusterModel, Cluster
from recommender.models import Preference, Recommendation

@pytest.mark.django_db
def test_recommendation_links_preference_and_cluster():
    user = User.objects.create_user("u", email="u@example.com", password="x")
    pref = Preference.objects.create(user=user, role_target="developer",
        budget_min_idr=8000000, budget_max_idr=20000000, min_ram_gb=16,
        min_processor_tier=5, min_storage_gb=512)
    cm = ClusterModel.objects.create(k_optimal=3, silhouette_score=0.6, centroids=[],
        wcss_list=[], silhouette_list=[], scaler_params={}, feature_order=[], is_active=True)
    cl = Cluster.objects.create(cluster_model=cm, label=1, interpretation="Mid-Range",
        centroid=[], member_count=5, summary={})
    rec = Recommendation.objects.create(user=user, preference=pref, cluster_model=cm,
        selected_cluster=cl, results=[{"id":1,"similarity":0.9}], precision_at_k=0.8, k_value=5)
    assert rec.preference == pref
    assert rec.selected_cluster.interpretation == "Mid-Range"
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest recommender/tests/test_models.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement models**

`recommender/models.py`:
```python
from django.contrib.auth.models import User
from django.db import models
from clustering.models import ClusterModel, Cluster

class Preference(models.Model):
    ROLE_CHOICES = [("developer","Developer"),("designer","UI/UX Designer"),
                    ("business_analyst","Business Analyst"),("manajemen","Staf Manajemen")]
    STORAGE_CHOICES = [("SSD","SSD"),("HDD","HDD")]
    VGA_CHOICES = [("integrated","Integrated"),("dedicated","Dedicated")]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="preferences")
    role_target = models.CharField(max_length=20, choices=ROLE_CHOICES)
    budget_min_idr = models.BigIntegerField()
    budget_max_idr = models.BigIntegerField()
    min_ram_gb = models.PositiveIntegerField()
    min_processor_tier = models.PositiveSmallIntegerField()
    min_storage_gb = models.PositiveIntegerField()
    storage_type = models.CharField(max_length=3, choices=STORAGE_CHOICES, blank=True)
    vga_type = models.CharField(max_length=10, choices=VGA_CHOICES, blank=True)
    min_screen_inch = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    min_battery_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    brand_preference = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

class Recommendation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recommendations")
    preference = models.ForeignKey(Preference, on_delete=models.CASCADE, related_name="recommendations")
    cluster_model = models.ForeignKey(ClusterModel, on_delete=models.CASCADE)
    selected_cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    results = models.JSONField()
    precision_at_k = models.FloatField()
    k_value = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
```

- [ ] **Step 4: Migrate + run test**

Run: `uv run python manage.py makemigrations recommender && uv run pytest recommender/tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(recommender): Preference + Recommendation models"
```

---

## Task 11: recommender services — preference→vector + full recommend flow

**Files:**
- Create: `recommender/services.py`, `recommender/tests/test_services.py`

Key alignment: a Preference must become a record shaped like a Laptop so `clustering.engine.preprocess` (reusing saved `scaler_params`/`feature_order`) maps it into the same feature space. Map min specs → representative values; for missing optional fields use the cluster-neutral midpoint (the preprocess clamps to [0,1] anyway).

- [ ] **Step 1: Write failing test**

`recommender/tests/test_services.py`:
```python
import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from clustering.services import run_training
from recommender.models import Preference, Recommendation
from recommender.services import generate_recommendation, NoActiveModel

@pytest.mark.django_db
def test_generate_recommendation_end_to_end():
    call_command("generate_dummy_laptops", "--count", "80", "--seed", "3")
    run_training()
    user = User.objects.create_user("u", email="u@example.com", password="x")
    pref = Preference.objects.create(user=user, role_target="developer",
        budget_min_idr=8000000, budget_max_idr=25000000, min_ram_gb=16,
        min_processor_tier=5, min_storage_gb=512)
    rec = generate_recommendation(pref, top_n=5)
    assert isinstance(rec, Recommendation)
    assert len(rec.results) <= 5
    assert 0.0 <= rec.precision_at_k <= 1.0
    # results sorted by similarity desc
    sims = [r["similarity"] for r in rec.results]
    assert sims == sorted(sims, reverse=True)

@pytest.mark.django_db
def test_generate_recommendation_without_active_model():
    user = User.objects.create_user("u2", email="u2@example.com", password="x")
    pref = Preference.objects.create(user=user, role_target="manajemen",
        budget_min_idr=5000000, budget_max_idr=12000000, min_ram_gb=8,
        min_processor_tier=3, min_storage_gb=256)
    with pytest.raises(NoActiveModel):
        generate_recommendation(pref, top_n=5)
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest recommender/tests/test_services.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement service**

`recommender/services.py`:
```python
from catalog.models import Laptop
from clustering import engine as cengine
from clustering.models import ClusterModel
from clustering.services import FIELDS
from recommender import engine as rengine
from recommender.models import Recommendation

class NoActiveModel(Exception):
    pass

def _pref_to_record(pref):
    """Shape a Preference like a Laptop record for preprocess."""
    return {
        "brand": pref.brand_preference or "ASUS",
        "processor_tier": pref.min_processor_tier,
        "ram_gb": pref.min_ram_gb,
        "storage_gb": pref.min_storage_gb,
        "storage_type": pref.storage_type or "SSD",
        "vga_type": pref.vga_type or "integrated",
        "screen_inch": float(pref.min_screen_inch) if pref.min_screen_inch else 14.0,
        "battery_hours": float(pref.min_battery_hours) if pref.min_battery_hours else 6.0,
        "price_idr": pref.budget_max_idr,
    }

def _pref_dict(pref):
    return {
        "budget_min_idr": pref.budget_min_idr, "budget_max_idr": pref.budget_max_idr,
        "min_ram_gb": pref.min_ram_gb, "min_processor_tier": pref.min_processor_tier,
        "min_storage_gb": pref.min_storage_gb,
        "min_screen_inch": float(pref.min_screen_inch) if pref.min_screen_inch else None,
        "min_battery_hours": float(pref.min_battery_hours) if pref.min_battery_hours else None,
        "storage_type": pref.storage_type or None, "vga_type": pref.vga_type or None,
        "brand_preference": pref.brand_preference or None,
    }

def generate_recommendation(pref, top_n=5):
    model = ClusterModel.objects.filter(is_active=True).first()
    if model is None:
        raise NoActiveModel("Admin belum melakukan training cluster.")

    # build preference vector in training feature space
    pref_matrix, _, _ = cengine.preprocess(
        [_pref_to_record(pref)], scaler_params=model.scaler_params,
        feature_order=model.feature_order)
    pref_vector = pref_matrix[0]

    cluster_label = rengine.pick_cluster(pref_vector, model.centroids)
    selected_cluster = model.clusters.get(label=cluster_label)

    laptops = list(Laptop.objects.filter(cluster_label=cluster_label))
    lap_records = [{f: getattr(l, f) for f in FIELDS} | {"id": l.id, "name": str(l)} for l in laptops]
    lap_matrix, _, _ = cengine.preprocess(
        [{f: r[f] for f in FIELDS} for r in lap_records],
        scaler_params=model.scaler_params, feature_order=model.feature_order)
    for rec, vec in zip(lap_records, lap_matrix):
        rec["vector"] = vec

    top = rengine.cosine_topn(pref_vector, lap_records, n=top_n)
    pref_d = _pref_dict(pref)
    results = []
    for t in top:
        relevant = rengine.is_relevant(t, pref_d)
        results.append({
            "id": t["id"], "name": t["name"], "brand": t["brand"],
            "processor_tier": t["processor_tier"], "ram_gb": t["ram_gb"],
            "storage_gb": t["storage_gb"], "price_idr": t["price_idr"],
            "similarity": round(t["similarity"], 4), "relevant": relevant,
        })
    precision = rengine.precision_at_k(results, k=top_n)

    return Recommendation.objects.create(
        user=pref.user, preference=pref, cluster_model=model,
        selected_cluster=selected_cluster, results=results,
        precision_at_k=precision, k_value=top_n)
```

- [ ] **Step 4: Run test, verify passes**

Run: `uv run pytest recommender/tests/test_services.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat(recommender): preference->vector alignment + recommend service"
```

---

## Task 12: recommender forms + views (HTMX) + history

**Files:**
- Create: `recommender/forms.py`, `recommender/views.py`, `recommender/urls.py`, `recommender/tests/test_views.py`
- Modify: `config/urls.py`

- [ ] **Step 1: Write failing view tests**

`recommender/tests/test_views.py`:
```python
import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse
from clustering.services import run_training

@pytest.fixture
def user_client(client, db):
    user = User.objects.create_user("u", email="u@example.com", password="x")
    client.force_login(user)
    return client, user

@pytest.mark.django_db
def test_recommend_post_returns_results_partial(user_client):
    client, user = user_client
    call_command("generate_dummy_laptops", "--count", "80", "--seed", "5")
    run_training()
    resp = client.post(reverse("recommender:recommend"), {
        "role_target": "developer", "budget_min_idr": 8000000,
        "budget_max_idr": 25000000, "min_ram_gb": 16,
        "min_processor_tier": 5, "min_storage_gb": 512,
    }, HTTP_HX_REQUEST="true")
    assert resp.status_code == 200
    assert b"Precision" in resp.content or b"precision" in resp.content

@pytest.mark.django_db
def test_recommend_without_active_model_shows_message(user_client):
    client, user = user_client
    resp = client.post(reverse("recommender:recommend"), {
        "role_target": "manajemen", "budget_min_idr": 5000000,
        "budget_max_idr": 12000000, "min_ram_gb": 8,
        "min_processor_tier": 3, "min_storage_gb": 256,
    }, HTTP_HX_REQUEST="true")
    assert resp.status_code == 200
    assert "training".encode() in resp.content.lower()
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest recommender/tests/test_views.py -v`
Expected: FAIL (no url `recommender:recommend`).

- [ ] **Step 3: Implement form**

`recommender/forms.py`: `PreferenceForm(forms.ModelForm)` with `Meta.model = Preference`, fields all editable preference fields, widgets styled with FlyonUI/Tailwind classes (e.g. `class="input"`, `class="select"`). Mark optional fields `required=False`.

- [ ] **Step 4: Implement views + urls**

`recommender/views.py`:
```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, View
from .forms import PreferenceForm
from .models import Recommendation
from .services import generate_recommendation, NoActiveModel

class RecommendView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "recommender/recommend.html", {"form": PreferenceForm()})

    def post(self, request):
        form = PreferenceForm(request.POST)
        if not form.is_valid():
            return render(request, "recommender/_form.html", {"form": form})
        pref = form.save(commit=False)
        pref.user = request.user
        pref.save()
        try:
            rec = generate_recommendation(pref, top_n=5)
        except NoActiveModel as e:
            return render(request, "recommender/_no_model.html", {"message": str(e)})
        return render(request, "recommender/_results.html", {"rec": rec})

class HistoryView(LoginRequiredMixin, ListView):
    template_name = "recommender/history.html"
    context_object_name = "recommendations"
    def get_queryset(self):
        return Recommendation.objects.filter(user=self.request.user).select_related(
            "preference", "selected_cluster")
```
`recommender/urls.py` names: `recommender:recommend`, `recommender:history`. Register in `config/urls.py`: `path("recommend/", include("recommender.urls"))`.

- [ ] **Step 5: Create templates**

`recommender/recommend.html` (extends base, includes `_form.html` + empty `#results` div with `hx-target`), `_form.html` (form posts via `hx-post` to `recommender:recommend`, `hx-target="#results"`), `_results.html` (Top-N FlyonUI cards: name, specs, price, similarity badge, relevant badge; show selected cluster + Precision@K; handle empty results with note), `_no_model.html` (alert message), `history.html` (table of past recommendations).

- [ ] **Step 6: Run tests, verify pass**

Run: `uv run pytest recommender/tests/test_views.py -v`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "feat(recommender): preference form, htmx recommend view, history"
```

---

## Task 13: core app — base template, landing, role-aware dashboard

**Files:**
- Create: `core/views.py`, `core/urls.py`, `templates/base.html`, `core/templates/core/landing.html`, `core/templates/core/dashboard.html`, `core/tests/test_views.py`
- Modify: `config/urls.py`

- [ ] **Step 1: Write failing test**

`core/tests/test_views.py`:
```python
import pytest
from django.contrib.auth.models import User
from django.urls import reverse

@pytest.mark.django_db
def test_landing_accessible_anonymously(client):
    assert client.get(reverse("core:landing")).status_code == 200

@pytest.mark.django_db
def test_dashboard_requires_login(client):
    resp = client.get(reverse("core:dashboard"))
    assert resp.status_code in (302, 301)  # redirect to login

@pytest.mark.django_db
def test_admin_sees_admin_links(client):
    user = User.objects.create_user("a", email="a@example.com", password="x")
    user.profile.role = "admin"; user.profile.save()
    client.force_login(user)
    resp = client.get(reverse("core:dashboard"))
    assert b"clustering" in resp.content.lower() or b"training" in resp.content.lower()
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest core/tests/test_views.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement base.html**

`templates/base.html`: HTML5 skeleton loading Tailwind CDN, FlyonUI CDN (CSS + JS), and HTMX CDN (`https://unpkg.com/htmx.org`). Navbar uses FlyonUI components: brand, links conditional on `user.is_authenticated` and `user.profile.is_admin` (Catalog + Clustering for admin; Recommend + History for all logged-in; Login/Logout). `{% block content %}`. Add `{% load static %}`. Configure `TEMPLATES['DIRS'] = [BASE_DIR / "templates"]` in settings.

- [ ] **Step 4: Implement views + urls**

`core/views.py`:
```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

class LandingView(TemplateView):
    template_name = "core/landing.html"

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["is_admin"] = self.request.user.profile.is_admin
        return ctx
```
`core/urls.py` names `core:landing` (`""`), `core:dashboard` (`"dashboard/"`). In `config/urls.py`: `path("", include("core.urls"))`. Ensure `LOGIN_URL` points to allauth login.

- [ ] **Step 5: Implement landing + dashboard templates**

`landing.html`: hero explaining the system + "Login with Google" button (link to allauth google login). `dashboard.html`: role-aware cards — admin sees Catalog + Clustering links; all users see Recommend + History links.

- [ ] **Step 6: Run tests, verify pass + commit**

Run: `uv run pytest core/ -v`
Expected: PASS.
```bash
git add -A && git commit -m "feat(core): base template, landing, role-aware dashboard"
```

---

## Task 14: catalog views + templates (admin CRUD, HTMX)

**Files:**
- Create: `catalog/views.py`, `catalog/forms.py`, `catalog/urls.py`, `catalog/templates/catalog/list.html`, `catalog/templates/catalog/_row.html`, `catalog/templates/catalog/form.html`, `catalog/tests/test_views.py`
- Modify: `config/urls.py`

- [ ] **Step 1: Write failing tests for role guard + CRUD**

`catalog/tests/test_views.py`:
```python
import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from catalog.models import Laptop

def _admin(client):
    u = User.objects.create_user("a", email="a@example.com", password="x")
    u.profile.role = "admin"; u.profile.save(); client.force_login(u); return u

def _user(client):
    u = User.objects.create_user("u", email="u@example.com", password="x")
    client.force_login(u); return u

@pytest.mark.django_db
def test_user_forbidden_from_catalog(client):
    _user(client)
    assert client.get(reverse("catalog:list")).status_code == 403

@pytest.mark.django_db
def test_admin_can_list_and_create(client):
    _admin(client)
    assert client.get(reverse("catalog:list")).status_code == 200
    resp = client.post(reverse("catalog:create"), {
        "brand":"ASUS","model":"X","processor":"i5","processor_tier":5,
        "ram_gb":16,"storage_gb":512,"storage_type":"SSD","vga":"Iris",
        "vga_type":"integrated","screen_inch":14.0,"battery_hours":8.0,
        "price_idr":9500000})
    assert Laptop.objects.filter(brand="ASUS", model="X").exists()
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest catalog/tests/test_views.py -v`
Expected: FAIL.

- [ ] **Step 3: Implement form + views**

`catalog/forms.py`: `LaptopForm(forms.ModelForm)` with all editable fields (exclude `cluster_label`, timestamps), FlyonUI-styled widgets. `catalog/views.py`: `LaptopListView(AdminRequiredMixin, ListView)`, `LaptopCreateView(AdminRequiredMixin, CreateView)`, `LaptopUpdateView(AdminRequiredMixin, UpdateView)`, `LaptopDeleteView(AdminRequiredMixin, DeleteView)` — all `success_url = reverse_lazy("catalog:list")`. Import `AdminRequiredMixin` from `accounts.mixins`.

- [ ] **Step 4: Implement urls + templates**

`catalog/urls.py` names: `catalog:list`, `catalog:create`, `catalog:update` (`<int:pk>/edit/`), `catalog:delete` (`<int:pk>/delete/`). `config/urls.py`: `path("catalog/", include("catalog.urls"))`. Templates: `list.html` (FlyonUI table of laptops with edit/delete buttons + "Add laptop" link + training reminder), `form.html` (shared create/update form).

- [ ] **Step 5: Run tests, verify pass + commit**

Run: `uv run pytest catalog/tests/test_views.py -v`
Expected: PASS.
```bash
git add -A && git commit -m "feat(catalog): admin crud views + templates with role guard"
```

---

## Task 15: clustering dashboard templates (HTMX train + plots)

**Files:**
- Create: `clustering/templates/clustering/dashboard.html`, `clustering/templates/clustering/_train_result.html`, `clustering/templates/clustering/_train_error.html`
- Modify: `clustering/tests/test_views.py` (new file)

- [ ] **Step 1: Write failing view test**

`clustering/tests/test_views.py`:
```python
import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse

def _admin(client):
    u = User.objects.create_user("a", email="a@example.com", password="x")
    u.profile.role = "admin"; u.profile.save(); client.force_login(u); return u

@pytest.mark.django_db
def test_user_forbidden_from_clustering(client):
    u = User.objects.create_user("u", email="u@example.com", password="x")
    client.force_login(u)
    assert client.get(reverse("clustering:dashboard")).status_code == 403

@pytest.mark.django_db
def test_train_insufficient_data_returns_error_partial(client):
    _admin(client)
    call_command("generate_dummy_laptops", "--count", "5", "--seed", "9")
    resp = client.post(reverse("clustering:train"), HTTP_HX_REQUEST="true")
    assert resp.status_code == 200
    assert b"minimal" in resp.content.lower()

@pytest.mark.django_db
def test_train_success_returns_result_partial(client):
    _admin(client)
    call_command("generate_dummy_laptops", "--count", "60", "--seed", "9")
    resp = client.post(reverse("clustering:train"), HTTP_HX_REQUEST="true")
    assert resp.status_code == 200
    assert b"Silhouette" in resp.content or b"silhouette" in resp.content
```

- [ ] **Step 2: Run test, verify fails**

Run: `uv run pytest clustering/tests/test_views.py -v`
Expected: FAIL (templates missing / urls not wired).

- [ ] **Step 3: Implement templates**

`dashboard.html`: extends base; shows active ClusterModel summary (k_optimal, silhouette_score, created_at), Elbow + Silhouette plot `<img>` tags (`{{ model.elbow_plot.url }}`), cluster interpretation table; a "Train / Re-cluster" button with `hx-post="{% url 'clustering:train' %}"`, `hx-target="#train-output"`, `hx-indicator`. `_train_result.html`: plots + cluster table + success alert (must contain word "Silhouette"). `_train_error.html`: FlyonUI error alert echoing the `ValueError` message (contains "minimal").

- [ ] **Step 4: Run tests, verify pass + commit**

Run: `uv run pytest clustering/tests/test_views.py -v`
Expected: PASS.
```bash
git add -A && git commit -m "feat(clustering): dashboard + train result/error partials"
```

---

## Task 16: full suite, README, end-to-end smoke

**Files:**
- Create: `README.md`
- Modify: none (verification task)

- [ ] **Step 1: Run the full test suite**

Run: `uv run pytest -v`
Expected: all tests PASS. Fix any failures before continuing.

- [ ] **Step 2: Write README.md**

Cover: project purpose (1 paragraph tied to the skripsi), tech stack, prerequisites (PostgreSQL running, Google OAuth credentials), setup steps:
```bash
uv sync
cp .env.example .env   # fill in values
createdb laptop_recommender
uv run python manage.py migrate
uv run python manage.py generate_dummy_laptops --count 300
uv run python manage.py createsuperuser
uv run python manage.py runserver 8802
```
Then: Google OAuth manual setup (add Social App + Site in Django admin), admin allowlist via `ADMIN_EMAILS`, usage flow (admin trains cluster → user inputs preference → gets Top-N + Precision@K), evaluation metrics (Silhouette, Precision@K), and how to run tests (`uv run pytest`).

- [ ] **Step 3: Manual end-to-end smoke (documented, run locally)**

```bash
uv run python manage.py migrate
uv run python manage.py generate_dummy_laptops --count 300 --seed 1
uv run python manage.py runserver 8802
```
Verify: landing loads → login → (admin) train cluster shows plots → (user) submit preference shows Top-N + Precision@K → history lists the recommendation. Kill server with `pkill -f "manage.py runserver"`.

- [ ] **Step 4: Commit**

```bash
git add -A && git commit -m "docs: README with setup, oauth, usage, evaluation"
```

---

## Notes & Conventions

- **Engine purity:** `clustering/engine.py` and `recommender/engine.py` never import Django. All ORM access lives in `services.py`. This keeps the data-mining core unit-testable and matches the thesis algorithm sections.
- **Feature-space alignment (critical invariant):** the recommender always reuses `ClusterModel.scaler_params` + `feature_order` so the preference vector and laptop vectors share one space. Never re-fit a scaler at recommend time.
- **Single active model:** `ClusterModel.save()` enforces one `is_active=True`. Re-training creates a new versioned snapshot; old ones stay for history/comparison.
- **TDD:** every task is test-first. Run the named test, see it fail, implement, see it pass, commit.
- **Security note:** all admin views are guarded by `AdminRequiredMixin` (403 for non-admins). Google OAuth is the only auth path for end users; superuser/Django admin is for setup only.

