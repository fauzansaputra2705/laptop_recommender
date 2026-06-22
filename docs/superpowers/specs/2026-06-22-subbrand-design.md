# SubBrand Master Design

## Overview

Add `SubBrand` model to catalog app. SubBrand represents sub-brands within a parent Brand (e.g., ThinkPad under Lenovo, ROG under ASUS). Follows existing master table pattern (Brand, Processor, Gpu).

## Model

```python
class SubBrand(models.Model):
    name = models.CharField(max_length=50)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="sub_brands")

    class Meta:
        ordering = ["brand", "name"]
        unique_together = [("brand", "name")]
        verbose_name = "Sub Brand"
        verbose_name_plural = "Sub Brands"

    def __str__(self):
        return f"{self.brand.name} - {self.name}"
```

## Laptop Model Changes

Add optional FK:

```python
sub_brand = models.ForeignKey(
    SubBrand,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="laptops",
)
```

SET_NULL (not PROTECT) — sub_brand is optional, deletion shouldn't block Brand cleanup cascade concerns.

## Admin

```python
@admin.register(SubBrand)
class SubBrandAdmin(admin.ModelAdmin):
    list_display = ("name", "brand")
    list_filter = ("brand",)
    search_fields = ("name", "brand__name")
```

LaptopAdmin: add `sub_brand` to `list_display`, `list_filter`, `search_fields`.

## Views

Four CBVs following existing pattern:

| View | Parent | Mixin |
|------|--------|-------|
| `SubBrandListView` | `ListView` | `AdminRequiredMixin`, `DatatableViewMixin` |
| `SubBrandCreateView` | `CreateView` | `AdminRequiredMixin` |
| `SubBrandUpdateView` | `UpdateView` | `AdminRequiredMixin` |
| `SubBrandDeleteView` | `DeleteView` | `AdminRequiredMixin` |

## URLs

```python
# sub_brands
path("sub-brands/", SubBrandListView.as_view(), name="subbrand-list"),
path("sub-brands/create/", SubBrandCreateView.as_view(), name="subbrand-create"),
path("sub-brands/<int:pk>/edit/", SubBrandUpdateView.as_view(), name="subbrand-update"),
path("sub-brands/<int:pk>/delete/", SubBrandDeleteView.as_view(), name="subbrand-delete"),
```

## Templates

- `subbrand_list.html` — datatable list, columns: Name, Brand, Actions
- `subbrand_form.html` — create/update form (name + brand select)
- `subbrand_confirm_delete.html` — delete confirmation
- `_subbrand_actions.html` — row actions partial (edit/delete links)

## Forms

```python
class SubBrandForm(forms.ModelForm):
    class Meta:
        model = SubBrand
        fields = ["name", "brand"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "input input-bordered"}),
            "brand": forms.Select(attrs={"class": "select select-bordered"}),
        }
```

LaptopForm: add `"sub_brand"` to fields list (select dropdown).

## CSV Import

Optional `sub_brand` column. Resolve via `get_or_create` scoped to brand:

```python
if row.get("sub_brand"):
    sub_brand, _ = SubBrand.objects.get_or_create(
        name=row["sub_brand"], brand=brand_obj
    )
```

Validation: if `sub_brand` present but `brand` missing, raise error.

## Migration

1. Create `SubBrand` table
2. Add nullable `sub_brand` FK to `Laptop`

## Testing

- SubBrand CRUD views (admin auth required)
- unique_together constraint enforced
- Laptop optional FK works (null allowed)
- CSV import with/without sub_brand column

## Out of Scope

- HTMX dependent dropdown (brand → filter sub_brand options) — flat select showing all
- Preference model changes (no `sub_brand_preference` field)
- Clustering/recommender engine changes (sub_brand not a feature)
