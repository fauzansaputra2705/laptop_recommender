# HTMX Datatable Component Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable Django datatable component with HTMX-powered sorting, filtering, pagination, and row actions — then migrate all 5 existing list views to use it.

**Architecture:** New `datatable` Django app containing a `DatatableViewMixin` (parses GET params for sort/search/page), a `{% datatable %}` inclusion tag (renders Tailwind-styled table with HTMX), and partial templates for body/pagination swaps. Views define a `datatable_columns` config list; mixin does the rest.

**Tech Stack:** Django 5.x, HTMX 2.0.4 (already in base.html), Tailwind CSS (CDN, already in base.html), pytest-django

## Global Constraints

- Python 3.12+, Django 5.x
- HTMX 2.0.4 loaded globally in `templates/base.html`
- Tailwind via CDN (`cdn.tailwindcss.com`) — no build step
- `APP_DIRS: True` in TEMPLATES — app templates in `datatable/templates/datatable/`
- All UI text in Indonesian (match existing patterns)
- Dark mode support via `dark:` Tailwind classes
- Existing views use `ListView` + `paginate_by` + `AdminRequiredMixin`/`LoginRequiredMixin`

## File Structure

```
datatable/
  __init__.py              # empty
  apps.py                  # DatatableConfig
  mixins.py                # DatatableViewMixin
  templatetags/
    __init__.py            # empty
    datatable_tags.py      # {% datatable %} inclusion tag
  templates/
    datatable/
      table.html           # full component (search + table + pagination)
      _tbody.html           # partial: <tbody> rows only
      _pagination.html      # partial: pagination + per-page + count
tests/
  test_mixins.py           # pytest tests for mixin logic
```

---

### Task 1: Create datatable app with mixin, tag, and templates

**Files:**
- Create: `datatable/__init__.py`
- Create: `datatable/apps.py`
- Create: `datatable/mixins.py`
- Create: `datatable/templatetags/__init__.py`
- Create: `datatable/templatetags/datatable_tags.py`
- Create: `datatable/templates/datatable/table.html`
- Create: `datatable/templates/datatable/_tbody.html`
- Create: `datatable/templates/datatable/_pagination.html`
- Modify: `config/settings.py` — add `"datatable"` to INSTALLED_APPS

**Interfaces:**
- Produces: `DatatableViewMixin` class (used by views in Tasks 3-5)
- Produces: `{% datatable %}` template tag (used in Task 3-5 templates)
- Consumes: `context['datatable']` dict set by mixin in `get_context_data`

- [ ] **Step 1: Create app structure**

Create `datatable/__init__.py` (empty file):
```python
```

Create `datatable/apps.py`:
```python
from django.apps import AppConfig


class DatatableConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "datatable"
    label = "datatable"
```

Create `datatable/templatetags/__init__.py` (empty file):
```python
```

- [ ] **Step 2: Implement DatatableViewMixin**

Create `datatable/mixins.py`:
```python
from django.core.paginator import Paginator
from django.db.models import Q


class DatatableViewMixin:
    """Mixin for ListView that adds server-side sort/search/pagination for HTMX datatables.

    Usage:
        class MyView(DatatableViewMixin, ListView):
            datatable_columns = [
                {"key": "name", "label": "Nama"},
                {"key": "price", "label": "Harga", "searchable": False},
            ]
    """

    datatable_columns = []
    datatable_per_page_default = 20

    def get_datatable_queryset(self):
        """Override to customize the base queryset for the datatable.
        Defaults to get_queryset()."""
        return self.get_queryset()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        columns = self.datatable_columns
        qs = self.get_datatable_queryset()
        params = self.request.GET

        # --- search ---
        search = params.get("search", "").strip()
        if search:
            searchable = [c["key"] for c in columns if c.get("searchable", True)]
            q = Q()
            for field in searchable:
                q |= Q(**{f"{field}__icontains": search})
            qs = qs.filter(q)

        # --- sort ---
        sort_key = params.get("sort", "")
        sort_dir = params.get("dir", "asc")
        valid_keys = {c["key"] for c in columns if c.get("sortable", True)}
        if sort_key and sort_key in valid_keys:
            order = sort_key if sort_dir == "asc" else f"-{sort_key}"
            qs = qs.order_by(order)

        # --- paginate ---
        try:
            per_page = int(params.get("per_page", self.datatable_per_page_default))
        except (ValueError, TypeError):
            per_page = self.datatable_per_page_default
        per_page = max(10, min(per_page, 100))

        paginator = Paginator(qs, per_page)
        try:
            page_num = int(params.get("page", 1))
        except (ValueError, TypeError):
            page_num = 1
        page_obj = paginator.get_page(page_num)

        ctx["datatable"] = {
            "columns": columns,
            "page_obj": page_obj,
            "search": search,
            "sort_key": sort_key,
            "sort_dir": sort_dir,
            "per_page": per_page,
            "per_page_options": [10, 20, 50, 100],
            "request_path": self.request.path,
            "total_count": paginator.count,
        }
        return ctx
```

- [ ] **Step 3: Implement template tag**

Create `datatable/templatetags/datatable_tags.py`:
```python
from django import template

register = template.Library()


@register.inclusion_tag("datatable/table.html", takes_context=True)
def datatable(context):
    """Render a full HTMX datatable component.

    Expects context["datatable"] dict set by DatatableViewMixin.
    Usage in template:
        {% load datatable %}
        {% datatable %}
    """
    return context.get("datatable", {})
```

- [ ] **Step 4: Create templates**

Create `datatable/templates/datatable/table.html`:
```html
{# Full datatable component. Receives: columns, page_obj, search, sort_key, sort_dir, per_page, per_page_options, request_path, total_count #}
{% load humanize %}
{% if request.headers.HX-Request %}
  {# HTMX partial: return only tbody + pagination for swap #}
  {% include "datatable/_tbody.html" %}
  {% include "datatable/_pagination.html" %}
{% else %}
  {# Full page: search + table + pagination #}
  <div id="datatable-wrapper">
    {# ─── Search + Per Page controls ─── #}
    <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div class="relative max-w-sm flex-1">
        <svg class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
        <input type="text"
               name="search"
               value="{{ search }}"
               placeholder="Cari..."
               hx-get="{{ request_path }}"
               hx-trigger="keyup changed delay:300ms, search"
               hx-include="#datatable-controls"
               hx-target="#datatable-wrapper"
               hx-swap="innerHTML"
               class="w-full rounded-md border border-slate-300 bg-white py-2 pl-10 pr-3 text-sm placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100">
      </div>
      <div class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
        <span>{{ total_count }} data</span>
        <span class="text-slate-300 dark:text-slate-600">|</span>
        <label for="per-page-select" class="sr-only">Per halaman</label>
        <select id="per-page-select"
                name="per_page"
                hx-get="{{ request_path }}"
                hx-trigger="change"
                hx-include="#datatable-controls"
                hx-target="#datatable-wrapper"
                hx-swap="innerHTML"
                class="rounded border border-slate-300 bg-white px-2 py-1 text-sm dark:border-slate-600 dark:bg-slate-800">
          {% for opt in per_page_options %}
            <option value="{{ opt }}" {% if opt == per_page %}selected{% endif %}>{{ opt }}/halaman</option>
          {% endfor %}
        </select>
      </div>
    </div>

    {# Hidden form for hx-include to collect all controls #}
    <div id="datatable-controls" class="hidden">
      <input type="hidden" name="search" value="{{ search }}">
      <input type="hidden" name="per_page" value="{{ per_page }}">
      {% if sort_key %}<input type="hidden" name="sort" value="{{ sort_key }}">{% endif %}
      {% if sort_dir %}<input type="hidden" name="dir" value="{{ sort_dir }}">{% endif %}
    </div>

    {# ─── Table ─── #}
    {% if page_obj.object_list %}
      <div class="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <table class="min-w-full text-sm">
          <thead class="border-b border-slate-200 bg-slate-50 text-left dark:border-slate-700 dark:bg-slate-900">
            <tr>
              {% for col in columns %}
                <th class="px-4 py-3 font-semibold{% if forloop.last %} text-right{% endif %}">
                  {% if col.sortable|default:True %}
                    <a href="#"
                       hx-get="{{ request_path }}?{% if sort_key == col.key and sort_dir == 'asc' %}sort={{ col.key }}&dir=desc{% else %}sort={{ col.key }}&dir=asc{% endif %}{% if search %}&search={{ search }}{% endif %}&per_page={{ per_page }}"
                       hx-target="#datatable-wrapper"
                       hx-swap="innerHTML"
                       class="inline-flex items-center gap-1 hover:text-slate-900 dark:hover:text-white cursor-pointer">
                      {{ col.label }}
                      {% if sort_key == col.key %}
                        {% if sort_dir == 'asc' %}
                          <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"/></svg>
                        {% else %}
                          <svg class="h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
                        {% endif %}
                      {% endif %}
                    </a>
                  {% else %}
                    {{ col.label }}
                  {% endif %}
                </th>
              {% endfor %}
            </tr>
          </thead>
          <tbody id="datatable-tbody" class="divide-y divide-slate-100 dark:divide-slate-700">
            {% include "datatable/_tbody.html" %}
          </tbody>
        </table>
      </div>

      <div id="datatable-pagination">
        {% include "datatable/_pagination.html" %}
      </div>
    {% else %}
      <div class="rounded-lg border border-dashed border-slate-300 p-8 text-center text-sm text-slate-500 dark:border-slate-700">
        {% if search %}
          Tidak ada data yang cocok dengan pencarian "<strong>{{ search }}</strong>".
        {% else %}
          Belum ada data.
        {% endif %}
      </div>
    {% endif %}
  </div>
{% endif %}
```

Create `datatable/templates/datatable/_tbody.html`:
```html
{# Partial: table rows. Receives: columns, page_obj (from datatable context) #}
{% load humanize %}
{% for obj in page_obj.object_list %}
  <tr class="hover:bg-slate-50 dark:hover:bg-slate-700/50">
    {% for col in columns %}
      <td class="px-4 py-3{% if col.key == 'actions' or forloop.last %} text-right{% endif %}{% if col.mono|default:False %} mono{% endif %}">
        {% if col.template %}
          {% include col.template with object=obj column=col only %}
        {% else %}
          {{ obj|get_attr:col.key|default:"-" }}
        {% endif %}
      </td>
    {% endfor %}
  </tr>
{% endfor %}
```

Create `datatable/templates/datatable/_pagination.html`:
```html
{# Partial: pagination controls. Receives: page_obj, per_page, request_path, search, sort_key, sort_dir #}
{% if page_obj.paginator.num_pages > 1 %}
  <div class="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
    {# Page info #}
    <p class="text-sm text-slate-500 dark:text-slate-400">
      Menampilkan {{ page_obj.start_index }}-{{ page_obj.end_index }} dari {{ page_obj.paginator.count }} data
    </p>

    {# Page buttons #}
    <div class="flex items-center gap-1 text-sm">
      {# First #}
      {% if page_obj.number > 1 %}
        <a href="#"
           hx-get="{{ request_path }}?page=1{% if search %}&search={{ search }}{% endif %}{% if sort_key %}&sort={{ sort_key }}&dir={{ sort_dir }}{% endif %}&per_page={{ per_page }}"
           hx-target="#datatable-wrapper"
           hx-swap="innerHTML"
           class="rounded px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
           title="Halaman pertama">
          &laquo;
        </a>
      {% endif %}

      {# Previous #}
      {% if page_obj.has_previous %}
        <a href="#"
           hx-get="{{ request_path }}?page={{ page_obj.previous_page_number }}{% if search %}&search={{ search }}{% endif %}{% if sort_key %}&sort={{ sort_key }}&dir={{ sort_dir }}{% endif %}&per_page={{ per_page }}"
           hx-target="#datatable-wrapper"
           hx-swap="innerHTML"
           class="rounded px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer">
          &lsaquo;
        </a>
      {% endif %}

      {# Page numbers #}
      {% for num in page_obj.paginator.page_range %}
        {% if num == page_obj.number %}
          <span class="rounded bg-indigo-600 px-3 py-1 text-sm font-medium text-white">{{ num }}</span>
        {% elif num > page_obj.number|add:"-3" and num < page_obj.number|add:"3" %}
          <a href="#"
             hx-get="{{ request_path }}?page={{ num }}{% if search %}&search={{ search }}{% endif %}{% if sort_key %}&sort={{ sort_key }}&dir={{ sort_dir }}{% endif %}&per_page={{ per_page }}"
             hx-target="#datatable-wrapper"
             hx-swap="innerHTML"
             class="rounded px-3 py-1 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer">
            {{ num }}
          </a>
        {% elif num == 1 or num == page_obj.paginator.num_pages %}
          <a href="#"
             hx-get="{{ request_path }}?page={{ num }}{% if search %}&search={{ search }}{% endif %}{% if sort_key %}&sort={{ sort_key }}&dir={{ sort_dir }}{% endif %}&per_page={{ per_page }}"
             hx-target="#datatable-wrapper"
             hx-swap="innerHTML"
             class="rounded px-3 py-1 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer">
            {{ num }}
          </a>
        {% elif num == 2 or num == page_obj.paginator.num_pages|add:"-1" %}
          <span class="px-1 text-slate-400">&hellip;</span>
        {% endif %}
      {% endfor %}

      {# Next #}
      {% if page_obj.has_next %}
        <a href="#"
           hx-get="{{ request_path }}?page={{ page_obj.next_page_number }}{% if search %}&search={{ search }}{% endif %}{% if sort_key %}&sort={{ sort_key }}&dir={{ sort_dir }}{% endif %}&per_page={{ per_page }}"
           hx-target="#datatable-wrapper"
           hx-swap="innerHTML"
           class="rounded px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer">
          &rsaquo;
        </a>
      {% endif %}

      {# Last #}
      {% if page_obj.number < page_obj.paginator.num_pages %}
        <a href="#"
           hx-get="{{ request_path }}?page={{ page_obj.paginator.num_pages }}{% if search %}&search={{ search }}{% endif %}{% if sort_key %}&sort={{ sort_key }}&dir={{ sort_dir }}{% endif %}&per_page={{ per_page }}"
           hx-target="#datatable-wrapper"
           hx-swap="innerHTML"
           class="rounded px-2 py-1 hover:bg-slate-100 dark:hover:bg-slate-800 cursor-pointer"
           title="Halaman terakhir">
          &raquo;
        </a>
      {% endif %}
    </div>
  </div>
{% endif %}
```

- [ ] **Step 5: Add custom template filter for object attribute access**

The `_tbody.html` template uses `{{ obj|get_attr:col.key }}` to dynamically access object attributes. Create a custom filter.

Create `datatable/templatetags/datatable_tags.py` (update the file from Step 3):
```python
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
def get_attr(obj, attr):
    """Get an attribute from an object dynamically. Usage: {{ obj|get_attr:"field_name" }}"""
    try:
        value = getattr(obj, attr)
        if callable(value):
            return value()
        return value
    except AttributeError:
        return ""


@register.inclusion_tag("datatable/table.html", takes_context=True)
def datatable(context):
    """Render a full HTMX datatable component.

    Expects context["datatable"] dict set by DatatableViewMixin.
    Usage in template:
        {% load datatable %}
        {% datatable %}
    """
    return context.get("datatable", {})
```

- [ ] **Step 6: Register app in settings**

Modify `config/settings.py` — add `"datatable"` to `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # third-party
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    # local
    "accounts",
    "catalog",
    "clustering",
    "core",
    "datatable",
    "recommender",
]
```

- [ ] **Step 7: Commit**

```bash
git add datatable/ config/settings.py
git commit -m "feat(datatable): add reusable HTMX datatable component — mixin, tag, templates"
```

---

### Task 2: Write tests for DatatableViewMixin

**Files:**
- Create: `datatable/tests/__init__.py`
- Create: `datatable/tests/test_mixins.py`

**Interfaces:**
- Consumes: `DatatableViewMixin` from `datatable/mixins.py`
- Tests use `Laptop` model from `catalog.models` (existing, has data-friendly fields)

- [ ] **Step 1: Create test file**

Create `datatable/tests/__init__.py` (empty):
```python
```

Create `datatable/tests/test_mixins.py`:
```python
import pytest
from django.test import RequestFactory
from django.views.generic import ListView

from catalog.models import Laptop
from datatable.mixins import DatatableViewMixin


class LaptopDatatableView(DatatableViewMixin, ListView):
    model = Laptop
    template_name = "catalog/list.html"
    context_object_name = "laptops"
    datatable_columns = [
        {"key": "brand", "label": "Merek", "sortable": True, "searchable": True},
        {"key": "model", "label": "Model", "sortable": True, "searchable": True},
        {"key": "price_idr", "label": "Harga", "sortable": True, "searchable": False},
        {"key": "ram_gb", "label": "RAM", "sortable": True, "searchable": False},
    ]


@pytest.fixture
def laptops(db):
    """Create test laptops."""
    Laptop.objects.create(
        brand="Asus", model="VivoBook 14", processor="i5", processor_tier=5,
        ram_gb=8, storage_gb=256, storage_type="SSD", vga="Intel", vga_type="integrated",
        screen_inch=14.0, battery_hours=8.0, price_idr=8000000,
    )
    Laptop.objects.create(
        brand="Lenovo", model="IdeaPad Slim 3", processor="i3", processor_tier=3,
        ram_gb=4, storage_gb=256, storage_type="SSD", vga="Intel", vga_type="integrated",
        screen_inch=14.0, battery_hours=7.0, price_idr=6000000,
    )
    Laptop.objects.create(
        brand="Asus", model="ROG Zephyrus", processor="i9", processor_tier=9,
        ram_gb=32, storage_gb=1024, storage_type="SSD", vga="RTX 4060", vga_type="dedicated",
        screen_inch=15.6, battery_hours=5.0, price_idr=25000000,
    )


@pytest.mark.django_db
class TestDatatableViewMixin:
    def _get_view(self, query_params=""):
        factory = RequestFactory()
        request = factory.get(f"/test/{query_params}")
        view = LaptopDatatableView.as_view()
        return request, view

    def test_default_context_contains_datatable(self, laptops):
        request, view = self._get_view()
        response = view(request)
        response.render()
        ctx = response.context_data
        assert "datatable" in ctx
        dt = ctx["datatable"]
        assert dt["total_count"] == 3
        assert dt["search"] == ""
        assert dt["sort_key"] == ""
        assert dt["per_page"] == 20

    def test_search_filters_results(self, laptops):
        request, view = self._get_view("?search=asus")
        response = view(request)
        dt = response.context_data["datatable"]
        assert dt["total_count"] == 2
        assert dt["search"] == "asus"

    def test_search_no_results(self, laptops):
        request, view = self._get_view("?search=dell")
        response = view(request)
        dt = response.context_data["datatable"]
        assert dt["total_count"] == 0

    def test_sort_ascending(self, laptops):
        request, view = self._get_view("?sort=price_idr&dir=asc")
        response = view(request)
        dt = response.context_data["datatable"]
        prices = [obj.price_idr for obj in dt["page_obj"].object_list]
        assert prices == sorted(prices)

    def test_sort_descending(self, laptops):
        request, view = self._get_view("?sort=price_idr&dir=desc")
        response = view(request)
        dt = response.context_data["datatable"]
        prices = [obj.price_idr for obj in dt["page_obj"].object_list]
        assert prices == sorted(prices, reverse=True)

    def test_pagination(self, laptops):
        request, view = self._get_view("?per_page=2&page=1")
        response = view(request)
        dt = response.context_data["datatable"]
        assert len(dt["page_obj"].object_list) == 2
        assert dt["page_obj"].has_next()

    def test_pagination_page_2(self, laptops):
        request, view = self._get_view("?per_page=2&page=2")
        response = view(request)
        dt = response.context_data["datatable"]
        assert len(dt["page_obj"].object_list) == 1

    def test_per_page_clamped(self, laptops):
        request, view = self._get_view("?per_page=5")
        response = view(request)
        dt = response.context_data["datatable"]
        assert dt["per_page"] == 10  # clamped to min 10

    def test_invalid_page_defaults_to_1(self, laptops):
        request, view = self._get_view("?page=abc")
        response = view(request)
        dt = response.context_data["datatable"]
        assert dt["page_obj"].number == 1

    def test_search_and_sort_combined(self, laptops):
        request, view = self._get_view("?search=asus&sort=price_idr&dir=desc")
        response = view(request)
        dt = response.context_data["datatable"]
        assert dt["total_count"] == 2
        prices = [obj.price_idr for obj in dt["page_obj"].object_list]
        assert prices == sorted(prices, reverse=True)
```

- [ ] **Step 2: Run tests**

```bash
cd /Users/fauzan/LATIHAN/laptop_recommender && python -m pytest datatable/tests/test_mixins.py -v
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add datatable/tests/
git commit -m "test(datatable): add tests for DatatableViewMixin — search, sort, pagination"
```

---

### Task 3: Migrate catalog/list to use datatable component

**Files:**
- Modify: `catalog/views.py` — add `DatatableViewMixin`, define `datatable_columns`
- Modify: `catalog/templates/catalog/list.html` — replace table markup with `{% datatable %}`
- Create: `catalog/templates/catalog/_row_actions.html` — row actions partial

**Interfaces:**
- Consumes: `DatatableViewMixin` from `datatable.mixins`
- Consumes: `{% datatable %}` tag from `datatable_tags`
- Produces: proof-of-concept migration pattern for Tasks 4-5

- [ ] **Step 1: Update catalog view**

Modify `catalog/views.py`:
```python
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.mixins import AdminRequiredMixin
from datatable.mixins import DatatableViewMixin

from .forms import LaptopForm
from .models import Laptop


class LaptopListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = Laptop
    template_name = "catalog/list.html"
    context_object_name = "laptops"
    datatable_columns = [
        {"key": "brand", "label": "Merek", "sortable": True, "searchable": True},
        {"key": "model", "label": "Model", "sortable": True, "searchable": True},
        {"key": "processor_tier", "label": "Tier", "sortable": True, "searchable": False, "mono": True},
        {"key": "ram_gb", "label": "RAM", "sortable": True, "searchable": False, "mono": True},
        {"key": "storage_gb", "label": "Storage", "sortable": True, "searchable": False, "mono": True},
        {"key": "price_idr", "label": "Harga", "sortable": True, "searchable": False, "mono": True},
        {"key": "cluster_label", "label": "Cluster", "sortable": False, "searchable": False},
        {"key": "actions", "label": "Aksi", "sortable": False, "searchable": False, "template": "catalog/_row_actions.html"},
    ]


class LaptopCreateView(AdminRequiredMixin, CreateView):
    model = Laptop
    form_class = LaptopForm
    template_name = "catalog/form.html"
    success_url = reverse_lazy("catalog:list")


class LaptopUpdateView(AdminRequiredMixin, UpdateView):
    model = Laptop
    form_class = LaptopForm
    template_name = "catalog/form.html"
    success_url = reverse_lazy("catalog:list")


class LaptopDeleteView(AdminRequiredMixin, DeleteView):
    model = Laptop
    template_name = "catalog/confirm_delete.html"
    success_url = reverse_lazy("catalog:list")
```

- [ ] **Step 2: Create row actions template**

Create `catalog/templates/catalog/_row_actions.html`:
```html
<a href="{% url 'catalog:update' object.pk %}" class="font-medium text-indigo-600 hover:underline">Edit</a>
<a href="{% url 'catalog:delete' object.pk %}" class="ml-3 font-medium text-red-600 hover:underline">Hapus</a>
```

- [ ] **Step 3: Rewrite catalog list template**

Replace `catalog/templates/catalog/list.html`:
```html
{% extends "base.html" %}
{% load datatable humanize %}
{% block title %}Katalog Laptop{% endblock %}
{% block content %}
<div class="mb-6 flex items-center justify-between">
  <h1 class="text-2xl font-bold sm:text-3xl">Katalog Laptop</h1>
  <a href="{% url 'catalog:create' %}" class="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">+ Tambah Laptop</a>
</div>

{% datatable %}
{% endblock %}
```

- [ ] **Step 4: Verify template renders `actions` column correctly**

The `_row_actions.html` template uses `{% url 'catalog:update' object.pk %}` — `object` is passed by the datatable `_tbody.html` via `{% include col.template with object=obj column=col only %}`. Verify this works by checking the template inclusion chain.

The `_tbody.html` template needs to pass `object` not `obj` to the custom template. Let me verify the template uses the correct variable name.

Check `datatable/templates/datatable/_tbody.html` — it passes `object=obj`. The `_row_actions.html` uses `object.pk`. This is correct.

- [ ] **Step 5: Manual test**

Run the dev server and verify:
- Page loads with search, sort, pagination controls
- Search filters by brand/model
- Sort toggles on column headers
- Pagination works
- Row actions (Edit/Hapus) link correctly
- Dark mode renders properly

```bash
cd /Users/fauzan/LATIHAN/laptop_recommender && python manage.py runserver
```

Visit: http://localhost:8000/catalog/

- [ ] **Step 6: Commit**

```bash
git add catalog/ catalog/templates/catalog/
git commit -m "refactor(catalog): migrate laptop list to HTMX datatable component"
```

---

### Task 4: Migrate core admin views to datatable

**Files:**
- Modify: `core/views.py` — add mixin to `ProfileListView`, `ClusterModelListView`, `RecommendationListView`
- Modify: `core/templates/core/manage_users.html` — use `{% datatable %}`
- Modify: `core/templates/core/manage_models.html` — use `{% datatable %}`
- Modify: `core/templates/core/manage_recommendations.html` — use `{% datatable %}`
- Create: `core/templates/core/_user_actions.html`
- Create: `core/templates/core/_model_actions.html`

**Interfaces:**
- Consumes: `DatatableViewMixin` from `datatable.mixins`
- Consumes: `{% datatable %}` tag

- [ ] **Step 1: Update core views**

Modify `core/views.py` — update the three admin ListViews:

```python
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import ListView, TemplateView

from accounts.mixins import AdminRequiredMixin
from accounts.models import Profile
from clustering.models import ClusterModel
from datatable.mixins import DatatableViewMixin
from recommender.models import Recommendation


class LandingView(TemplateView):
    template_name = "core/landing.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        is_admin = self.request.user.profile.is_admin
        ctx["is_admin"] = is_admin

        if is_admin:
            from catalog.models import Laptop
            from clustering.models import Cluster
            from django.db.models import Avg

            ctx["total_laptops"] = Laptop.objects.count()
            ctx["total_clusters"] = Cluster.objects.filter(cluster_model__is_active=True).count()
            ctx["total_users"] = User.objects.count()
            ctx["total_recommendations"] = Recommendation.objects.count()
            ctx["avg_precision"] = Recommendation.objects.aggregate(
                avg=Avg("precision_at_k")
            )["avg"] or 0
            ctx["active_clusters"] = Cluster.objects.filter(
                cluster_model__is_active=True
            ).select_related("cluster_model").order_by("label")
            ctx["recent_recommendations"] = Recommendation.objects.select_related(
                "user", "preference", "selected_cluster"
            ).order_by("-created_at")[:5]
        else:
            user_recs = self.request.user.recommendations.select_related(
                "preference", "selected_cluster"
            )
            ctx["user_recommendation_count"] = user_recs.count()
            last = user_recs.first()
            ctx["user_last_precision"] = last.precision_at_k if last else None
            ctx["user_last_date"] = last.created_at if last else None
            ctx["user_recent_recommendations"] = user_recs[:5]

        return ctx


class AdminLoginView(View):
    def post(self, request):
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return HttpResponseRedirect(reverse("core:dashboard"))
        return HttpResponseRedirect(reverse("account_login") + "?error=1")


# --- Admin Management Views ---

class ProfileListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = User
    template_name = "core/manage_users.html"
    context_object_name = "users"
    datatable_columns = [
        {"key": "username", "label": "Username", "sortable": True, "searchable": True},
        {"key": "email", "label": "Email", "sortable": False, "searchable": True},
        {"key": "role", "label": "Role", "sortable": False, "searchable": False},
        {"key": "is_staff", "label": "Staff", "sortable": True, "searchable": False},
        {"key": "date_joined", "label": "Bergabung", "sortable": True, "searchable": False},
        {"key": "actions", "label": "Aksi", "sortable": False, "searchable": False, "template": "core/_user_actions.html"},
    ]

    def get_queryset(self):
        return User.objects.select_related("profile").order_by("-date_joined")


class ToggleRoleView(AdminRequiredMixin, View):
    def post(self, request, pk):
        try:
            user = User.objects.select_related("profile").get(pk=pk)
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse("core:manage_users"))
        profile = user.profile
        profile.role = "user" if profile.is_admin else "admin"
        profile.save()
        return HttpResponseRedirect(reverse("core:manage_users"))


class ClusterModelListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = ClusterModel
    template_name = "core/manage_models.html"
    context_object_name = "models"
    datatable_columns = [
        {"key": "pk", "label": "ID", "sortable": True, "searchable": False},
        {"key": "k_optimal", "label": "K Optimal", "sortable": True, "searchable": False, "mono": True},
        {"key": "silhouette_score", "label": "Silhouette", "sortable": True, "searchable": False, "mono": True},
        {"key": "is_active", "label": "Status", "sortable": False, "searchable": False},
        {"key": "created_at", "label": "Dibuat", "sortable": True, "searchable": False},
        {"key": "actions", "label": "Aksi", "sortable": False, "searchable": False, "template": "core/_model_actions.html"},
    ]


class ActivateModelView(AdminRequiredMixin, View):
    def post(self, request, pk):
        try:
            model = ClusterModel.objects.get(pk=pk)
        except ClusterModel.DoesNotExist:
            return HttpResponseRedirect(reverse("core:manage_models"))
        model.is_active = True
        model.save()
        return HttpResponseRedirect(reverse("core:manage_models"))


class RecommendationListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = Recommendation
    template_name = "core/manage_recommendations.html"
    context_object_name = "recommendations"
    datatable_columns = [
        {"key": "pk", "label": "ID", "sortable": True, "searchable": False},
        {"key": "user__username", "label": "User", "sortable": True, "searchable": True},
        {"key": "preference__role_target", "label": "Role Target", "sortable": False, "searchable": True},
        {"key": "precision_at_k", "label": "Precision@K", "sortable": True, "searchable": False, "mono": True},
        {"key": "created_at", "label": "Tanggal", "sortable": True, "searchable": False},
    ]

    def get_queryset(self):
        return Recommendation.objects.select_related(
            "user", "preference", "selected_cluster", "cluster_model"
        ).order_by("-created_at")
```

- [ ] **Step 2: Create user actions template**

Create `core/templates/core/_user_actions.html`:
```html
{% if object.pk != request.user.pk %}
  <form method="post" action="{% url 'core:toggle_role' object.pk %}" class="inline">
    {% csrf_token %}
    <button type="submit" class="font-medium text-indigo-600 hover:underline cursor-pointer">
      {% if object.profile.is_admin %}Jadikan User{% else %}Jadikan Admin{% endif %}
    </button>
  </form>
{% else %}
  <span class="text-xs text-slate-400">(Anda)</span>
{% endif %}
```

- [ ] **Step 3: Create model actions template**

Create `core/templates/core/_model_actions.html`:
```html
{% if not object.is_active %}
  <form method="post" action="{% url 'core:activate_model' object.pk %}" class="inline">
    {% csrf_token %}
    <button type="submit" class="font-medium text-emerald-600 hover:underline cursor-pointer">Aktifkan</button>
  </form>
{% else %}
  <span class="text-xs text-slate-400">Sudah aktif</span>
{% endif %}
```

- [ ] **Step 4: Rewrite manage_users template**

Replace `core/templates/core/manage_users.html`:
```html
{% extends "base.html" %}
{% load datatable %}
{% block title %}Kelola Pengguna{% endblock %}
{% block content %}
<div class="mb-6 flex items-center justify-between">
  <h1 class="text-2xl font-bold sm:text-3xl">Kelola Pengguna</h1>
  <a href="{% url 'core:dashboard' %}" class="text-sm text-blue-600 hover:underline">&larr; Dashboard</a>
</div>

{% datatable %}
{% endblock %}
```

- [ ] **Step 5: Rewrite manage_models template**

Replace `core/templates/core/manage_models.html`:
```html
{% extends "base.html" %}
{% load datatable %}
{% block title %}Kelola Model Clustering{% endblock %}
{% block content %}
<div class="mb-6 flex items-center justify-between">
  <h1 class="text-2xl font-bold sm:text-3xl">Kelola Model Clustering</h1>
  <a href="{% url 'core:dashboard' %}" class="text-sm text-blue-600 hover:underline">&larr; Dashboard</a>
</div>

{% datatable %}
{% endblock %}
```

- [ ] **Step 6: Rewrite manage_recommendations template**

Replace `core/templates/core/manage_recommendations.html`:
```html
{% extends "base.html" %}
{% load datatable humanize %}
{% block title %}Semua Rekomendasi{% endblock %}
{% block content %}
<div class="mb-6 flex items-center justify-between">
  <h1 class="text-2xl font-bold sm:text-3xl">Semua Rekomendasi</h1>
  <a href="{% url 'core:dashboard' %}" class="text-sm text-blue-600 hover:underline">&larr; Dashboard</a>
</div>

{% datatable %}
{% endblock %}
```

- [ ] **Step 7: Handle `role` and `user__username` column rendering**

The `role` column isn't a direct model field — it's `user.profile.is_admin`. The `get_attr` filter won't traverse relations. Need to handle this in the template or add a computed field.

For `manage_users`, the `role` and `is_staff` columns need custom display (badges). The simplest approach: add `template` to those column configs and create small partials.

Create `core/templates/core/_user_role_cell.html`:
```html
{% if object.profile.is_admin %}
  <span class="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900/30 dark:text-blue-400">Admin</span>
{% else %}
  <span class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-700 dark:text-slate-400">User</span>
{% endif %}
```

Create `core/templates/core/_user_staff_cell.html`:
```html
{% if object.is_staff %}
  <span class="text-emerald-600 dark:text-emerald-400">Ya</span>
{% else %}
  <span class="text-slate-400">Tidak</span>
{% endif %}
```

Create `core/templates/core/_model_status_cell.html`:
```html
{% if object.is_active %}
  <span class="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-medium text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400">Aktif</span>
{% else %}
  <span class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-700 dark:text-slate-400">Nonaktif</span>
{% endif %}
```

Update `core/views.py` column configs to use these templates:
```python
# In ProfileListView:
{"key": "role", "label": "Role", "sortable": False, "searchable": False, "template": "core/_user_role_cell.html"},
{"key": "is_staff", "label": "Staff", "sortable": True, "searchable": False, "template": "core/_user_staff_cell.html"},

# In ClusterModelListView:
{"key": "is_active", "label": "Status", "sortable": False, "searchable": False, "template": "core/_model_status_cell.html"},
```

Also need to handle `user__username` for RecommendationListView — the `get_attr` filter needs to support `__` lookups. Update the filter:

Modify `datatable/templatetags/datatable_tags.py`:
```python
@register.filter
def get_attr(obj, attr):
    """Get an attribute from an object dynamically. Supports __ lookups.
    Usage: {{ obj|get_attr:"field_name" }} or {{ obj|get_attr:"user__username" }}"""
    try:
        value = obj
        for part in attr.split("__"):
            value = getattr(value, part)
            if callable(value):
                value = value()
        return value
    except (AttributeError, TypeError):
        return ""
```

- [ ] **Step 8: Manual test all three pages**

```bash
cd /Users/fauzan/LATIHAN/laptop_recommender && python manage.py runserver
```

Visit:
- http://localhost:8000/admin/users/
- http://localhost:8000/admin/models/
- http://localhost:8000/admin/recommendations/

Verify: search, sort, pagination, row actions, dark mode.

- [ ] **Step 9: Commit**

```bash
git add core/ core/templates/core/
git commit -m "refactor(core): migrate manage_users, manage_models, manage_recommendations to HTMX datatable"
```

---

### Task 5: Migrate recommender/history to datatable

**Files:**
- Modify: `recommender/views.py` — add mixin to `HistoryView`
- Modify: `recommender/templates/recommender/history.html` — use `{% datatable %}`

**Interfaces:**
- Consumes: `DatatableViewMixin` from `datatable.mixins`
- Consumes: `{% datatable %}` tag

- [ ] **Step 1: Update recommender HistoryView**

Modify `recommender/views.py`:
```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView, View

from datatable.mixins import DatatableViewMixin
from .forms import PreferenceForm
from .models import Recommendation
from .services import NoActiveModel, generate_recommendation


class RecommendView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "recommender/recommend.html", {"form": PreferenceForm()})

    def post(self, request):
        form = PreferenceForm(request.POST)
        if not form.is_valid():
            return render(request, "recommender/_form.html", {"form": form})
        pref = form.save(commit=False)
        pref.user = self.request.user
        pref.save()
        try:
            rec = generate_recommendation(pref, top_n=5)
        except NoActiveModel as exc:
            return render(request, "recommender/_no_model.html", {"message": str(exc)})
        return render(request, "recommender/_results.html", {"rec": rec})


class HistoryView(LoginRequiredMixin, DatatableViewMixin, ListView):
    template_name = "recommender/history.html"
    context_object_name = "recommendations"
    datatable_columns = [
        {"key": "created_at", "label": "Tanggal", "sortable": True, "searchable": False},
        {"key": "preference__role_target", "label": "Peran", "sortable": False, "searchable": False},
        {"key": "preference__budget_max_idr", "label": "Budget Maks", "sortable": False, "searchable": False, "mono": True},
        {"key": "selected_cluster__interpretation", "label": "Cluster", "sortable": False, "searchable": False},
        {"key": "precision_at_k", "label": "Precision@K", "sortable": True, "searchable": False, "mono": True},
    ]

    def get_queryset(self):
        return Recommendation.objects.filter(
            user=self.request.user
        ).select_related("preference", "selected_cluster")
```

- [ ] **Step 2: Rewrite history template**

Replace `recommender/templates/recommender/history.html`:
```html
{% extends "base.html" %}
{% load datatable humanize %}
{% block title %}Riwayat Rekomendasi{% endblock %}
{% block content %}
<h1 class="mb-6 text-2xl font-bold sm:text-3xl">Riwayat Rekomendasi</h1>

{% datatable %}
{% endblock %}
```

- [ ] **Step 3: Handle nested attribute display**

The `preference__role_target` column uses `get_attr` with `__` lookup. The updated filter from Task 4 Step 7 handles this: `obj.preference.role_target`.

But `preference__budget_max_idr` needs `intcomma` formatting. The `get_attr` filter returns raw values. For formatted display, use a template.

Create `recommender/templates/recommender/_budget_cell.html`:
```html
{% load humanize %}
Rp{{ object.preference.budget_max_idr|intcomma }}
```

Create `recommender/templates/recommender/_cluster_cell.html`:
```html
{{ object.selected_cluster.interpretation|default:"-" }}
```

Create `recommender/templates/recommender/_precision_cell.html`:
```html
{% if object.precision_at_k >= 0.8 %}
  <span class="font-medium text-emerald-600">{{ object.precision_at_k|floatformat:2 }}</span>
{% elif object.precision_at_k >= 0.5 %}
  <span class="font-medium text-amber-600">{{ object.precision_at_k|floatformat:2 }}</span>
{% else %}
  <span class="font-medium text-red-600">{{ object.precision_at_k|floatformat:2 }}</span>
{% endif %}
```

Update `recommender/views.py` column configs:
```python
datatable_columns = [
    {"key": "created_at", "label": "Tanggal", "sortable": True, "searchable": False},
    {"key": "preference__role_target", "label": "Peran", "sortable": False, "searchable": False},
    {"key": "preference__budget_max_idr", "label": "Budget Maks", "sortable": False, "searchable": False, "template": "recommender/_budget_cell.html"},
    {"key": "selected_cluster__interpretation", "label": "Cluster", "sortable": False, "searchable": False, "template": "recommender/_cluster_cell.html"},
    {"key": "precision_at_k", "label": "Precision@K", "sortable": True, "searchable": False, "template": "recommender/_precision_cell.html"},
]
```

- [ ] **Step 4: Manual test**

```bash
cd /Users/fauzan/LATIHAN/laptop_recommender && python manage.py runserver
```

Visit: http://localhost:8000/recommender/history/

Verify: search, sort, pagination, cell formatting, dark mode.

- [ ] **Step 5: Commit**

```bash
git add recommender/ recommender/templates/recommender/
git commit -m "refactor(recommender): migrate history to HTMX datatable"
```

---

### Task 6: Run full test suite and final verification

**Files:** None (verification only)

- [ ] **Step 1: Run all tests**

```bash
cd /Users/fauzan/LATIHAN/laptop_recommender && python -m pytest -v
```

Expected: All existing tests + new datatable tests pass.

- [ ] **Step 2: Manual smoke test all pages**

Visit each migrated page and verify:
1. Search works (filters results)
2. Sort works (toggle asc/desc)
3. Pagination works (page numbers, prev/next, first/last)
4. Per-page selector works (10/20/50/100)
5. Row actions work (links, buttons)
6. Dark mode renders correctly
7. Empty state shows properly
8. No full page reload on HTMX interactions

Pages:
- http://localhost:8000/catalog/
- http://localhost:8000/admin/users/
- http://localhost:8000/admin/models/
- http://localhost:8000/admin/recommendations/
- http://localhost:8000/recommender/history/

- [ ] **Step 3: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix(datatable): minor fixes from smoke testing"
```
