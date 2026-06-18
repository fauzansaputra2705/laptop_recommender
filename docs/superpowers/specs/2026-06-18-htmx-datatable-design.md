# HTMX Datatable Component — Design Spec

**Date:** 2026-06-18
**Status:** Approved

## Problem

All list views (manage_users, catalog/list, manage_models, manage_recommendations, recommender/history) use static server-rendered tables with basic prev/next pagination and no sorting, filtering, or HTMX interaction. Each table duplicates ~50 lines of identical Tailwind markup. Adding features (sort, search) to one means copy-pasting to all.

## Solution

Reusable Django datatable component: `DatatableViewMixin` + `{% datatable %}` inclusion tag. Server-side processing via HTMX. One new Django app `datatable`.

## Architecture

### File Structure

```
datatable/
  __init__.py
  apps.py
  mixins.py              # DatatableViewMixin
  templatetags/
    __init__.py
    datatable_tags.py    # {% datatable %} tag
  templates/
    datatable/
      table.html         # inclusion template (full component)
      _tbody.html        # partial: tbody rows (HTMX swap target)
      _pagination.html   # partial: pagination + per-page controls
```

### DatatableViewMixin

```python
class DatatableViewMixin:
    datatable_columns = []  # list of column dicts
    datatable_per_page_default = 20

    def get_datatable_queryset(self):
        """Override to customize base queryset. Defaults to get_queryset()."""
        return self.get_queryset()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        columns = self.datatable_columns
        qs = self.get_datatable_queryset()
        request = self.request
        params = request.GET

        # --- search ---
        search = params.get('search', '').strip()
        if search:
            searchable = [c['key'] for c in columns if c.get('searchable', True)]
            q = Q()
            for field in searchable:
                q |= Q(**{f'{field}__icontains': search})
            qs = qs.filter(q)

        # --- sort ---
        sort_key = params.get('sort', '')
        sort_dir = params.get('dir', 'asc')
        valid_keys = {c['key'] for c in columns if c.get('sortable', True)}
        if sort_key and sort_key in valid_keys:
            order = sort_key if sort_dir == 'asc' else f'-{sort_key}'
            qs = qs.order_by(order)

        # --- paginate ---
        per_page = int(params.get('per_page', self.datatable_per_page_default))
        per_page = max(10, min(per_page, 100))
        paginator = Paginator(qs, per_page)
        page_num = int(params.get('page', 1))
        page_obj = paginator.get_page(page_num)

        ctx['datatable'] = {
            'columns': columns,
            'page_obj': page_obj,
            'search': search,
            'sort_key': sort_key,
            'sort_dir': sort_dir,
            'per_page': per_page,
            'per_page_options': [10, 20, 50, 100],
            'request_path': request.path,
            'total_count': paginator.count,
        }
        return ctx
```

### Column Config

```python
datatable_columns = [
    {'key': 'brand', 'label': 'Merek', 'sortable': True, 'searchable': True},
    {'key': 'price_idr', 'label': 'Harga', 'sortable': True, 'searchable': False},
    {'key': 'cluster_label', 'label': 'Cluster', 'sortable': False, 'searchable': False},
    {'key': 'actions', 'label': 'Aksi', 'sortable': False, 'searchable': False,
     'template': 'catalog/_row_actions.html'},
]
```

Fields:
- `key` — model field name (used for `{{ obj.key }}` and sort param)
- `label` — column header text
- `sortable` — default `True`
- `searchable` — default `True` (only for text/char fields)
- `template` — optional cell template (receives `object` and `column` in context)

### Template Tag

```python
from django import template
register = template.Library()

@register.inclusion_tag('datatable/table.html', takes_context=True)
def datatable(context):
    return context.get('datatable', {})
```

Usage:
```html
{% load datatable %}
{% datatable %}
```

No arguments — mixin puts everything in `context['datatable']`.

### Inclusion Template — table.html

Full component renders:
1. **Search bar** — input with `hx-get` + `hx-trigger="keyup changed delay:300ms"` + `hx-include="[name='search']"` + `hx-target="#datatable-content"`
2. **Table** — `<thead>` with sortable headers (click → `hx-get` with sort params, arrow indicator), `<tbody>` with rows
3. **Footer** — pagination (first/prev/page numbers/next/last) + per-page select + record count

HTMX targets:
- `#datatable-tbody` — swap on sort/search/page change
- `#datatable-pagination` — swap on page/per-page change

### HTMX Request Pattern

```
GET {request_path}?sort={key}&dir={asc|desc}&search={query}&page={n}&per_page={n}
```

All parameters in GET query string. HTMX requests include `HX-Request: true` header — view can detect and return partial (tbody+pagination only) vs full page.

### Partial Response

Inclusion tag handles partial vs full rendering. `table.html` checks `{% if request.headers.HX-Request %}`:
- **HTMX request**: render only `_tbody.html` + `_pagination.html` (lightweight swap)
- **Full page load**: render complete `table.html` (search + table + pagination)

No view-level template switching needed. The tag does it all.

### Row Actions Template

Custom cell templates receive `object` (the row instance) and `column` (the column config dict) in context.

```html
{# catalog/_row_actions.html #}
{# receives: object (row instance), column (config dict) #}
<a href="{% url 'catalog:update' object.pk %}" class="font-medium text-indigo-600 hover:underline">Edit</a>
<button hx-delete="{% url 'catalog:delete' object.pk %}"
        hx-confirm="Yakin hapus?"
        hx-target="closest tr"
        hx-swap="outerHTML"
        class="ml-3 font-medium text-red-600 hover:underline cursor-pointer">Hapus</button>
```

Delete: `hx-target="closest tr"` + `hx-swap="outerHTML"` removes the row. Server returns `HttpResponse(status=200)` with empty body (or `HX-Trigger: refreshTable` header).

### Styling

Matches existing Tailwind patterns from manage_users.html / catalog/list.html:
- Container: `overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800`
- Header: `border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-900`
- Rows: `divide-y divide-slate-100 dark:divide-slate-700` + `hover:bg-slate-50 dark:hover:bg-slate-700/50`
- Search input: `rounded-md border border-slate-300 px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800`
- Pagination buttons: `rounded px-3 py-1 hover:bg-slate-100 dark:hover:bg-slate-800`

## Migration Plan

Refactor existing views one at a time:
1. catalog/list (most complete table, has pagination)
2. manage_users
3. manage_models
4. manage_recommendations
5. recommender/history

Each refactor: add mixin to view class, define `datatable_columns`, remove duplicated table markup from template.

## What We're NOT Building

- Client-side sorting/filtering (server-side only)
- Column visibility toggle
- Column reordering
- Export (CSV/Excel)
- Row selection/bulk actions
- Infinite scroll

YAGNI. Add when needed.

## Testing

- Manual: each refactored page works with sort/search/pagination/per_page
- HTMX partial swap works (no full page reload on interaction)
- Dark mode renders correctly
- Empty state shows properly
