from decimal import Decimal

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from django.contrib.auth.mixins import LoginRequiredMixin

from accounts.mixins import AdminRequiredMixin
from datatable.mixins import DatatableViewMixin

from .csv_import import parse_and_validate
from .forms import BrandForm, GpuForm, LaptopForm, ProcessorForm, SubBrandForm
from .models import Brand, Gpu, Laptop, Processor, SubBrand


class SubBrandApiView(LoginRequiredMixin, View):
    def get(self, request):
        brand_id = request.GET.get("brand")
        if not brand_id:
            return JsonResponse([], safe=False)
        sbs = SubBrand.objects.filter(brand_id=brand_id).order_by("name").values("id", "name")
        return JsonResponse(list(sbs), safe=False)


class LaptopBrowseView(LoginRequiredMixin, ListView):
    model = Laptop
    template_name = "catalog/browse.html"
    context_object_name = "laptops"
    paginate_by = 20

    def get_queryset(self):
        qs = Laptop.objects.select_related("brand", "processor", "vga")
        brand = self.request.GET.get("brand")
        if brand:
            qs = qs.filter(brand_id=brand)
        budget_min = self.request.GET.get("budget_min")
        if budget_min:
            qs = qs.filter(price_idr__gte=int(budget_min))
        budget_max = self.request.GET.get("budget_max")
        if budget_max:
            qs = qs.filter(price_idr__lte=int(budget_max))
        return qs.order_by("brand__name", "model")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["brands"] = Brand.objects.order_by("name")
        ctx["selected_brand"] = self.request.GET.get("brand", "")
        ctx["budget_min"] = self.request.GET.get("budget_min", "")
        ctx["budget_max"] = self.request.GET.get("budget_max", "")
        return ctx


class LaptopListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = Laptop
    template_name = "catalog/list.html"
    context_object_name = "laptops"
    datatable_columns = [
        {"key": "brand", "label": "Merek", "sortable": True, "searchable": True, "search_key": "brand__name", "sort_key": "brand__name"},
        {"key": "model", "label": "Model", "sortable": True, "searchable": True},
        {"key": "processor", "label": "Prosesor", "sortable": True, "searchable": True, "search_key": "processor__name", "sort_key": "processor__name"},
        {"key": "ram_gb", "label": "RAM", "sortable": True, "searchable": False, "mono": True, "template": "catalog/_ram_cell.html"},
        {"key": "storage_gb", "label": "Storage", "sortable": True, "searchable": False, "mono": True, "template": "catalog/_storage_cell.html"},
        {"key": "price_idr", "label": "Harga", "sortable": True, "searchable": False, "mono": True, "template": "catalog/_price_cell.html"},
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


# ─── Brand CRUD ───────────────────────────────────────────────────


class BrandListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = Brand
    template_name = "catalog/brand_list.html"
    context_object_name = "brands"
    datatable_columns = [
        {"key": "name", "label": "Nama Merek", "sortable": True, "searchable": True},
        {"key": "actions", "label": "Aksi", "sortable": False, "searchable": False, "template": "catalog/_brand_actions.html"},
    ]


class BrandCreateView(AdminRequiredMixin, CreateView):
    model = Brand
    form_class = BrandForm
    template_name = "catalog/brand_form.html"
    success_url = reverse_lazy("catalog:brand_list")


class BrandUpdateView(AdminRequiredMixin, UpdateView):
    model = Brand
    form_class = BrandForm
    template_name = "catalog/brand_form.html"
    success_url = reverse_lazy("catalog:brand_list")


class BrandDeleteView(AdminRequiredMixin, DeleteView):
    model = Brand
    template_name = "catalog/brand_confirm_delete.html"
    success_url = reverse_lazy("catalog:brand_list")


# ─── Processor CRUD ───────────────────────────────────────────────


class ProcessorListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = Processor
    template_name = "catalog/processor_list.html"
    context_object_name = "processors"
    datatable_columns = [
        {"key": "name", "label": "Nama Prosesor", "sortable": True, "searchable": True},
        {"key": "tier", "label": "Tier", "sortable": True, "searchable": False, "mono": True},
        {"key": "actions", "label": "Aksi", "sortable": False, "searchable": False, "template": "catalog/_processor_actions.html"},
    ]


class ProcessorCreateView(AdminRequiredMixin, CreateView):
    model = Processor
    form_class = ProcessorForm
    template_name = "catalog/processor_form.html"
    success_url = reverse_lazy("catalog:processor_list")


class ProcessorUpdateView(AdminRequiredMixin, UpdateView):
    model = Processor
    form_class = ProcessorForm
    template_name = "catalog/processor_form.html"
    success_url = reverse_lazy("catalog:processor_list")


class ProcessorDeleteView(AdminRequiredMixin, DeleteView):
    model = Processor
    template_name = "catalog/processor_confirm_delete.html"
    success_url = reverse_lazy("catalog:processor_list")


# ─── Gpu CRUD ─────────────────────────────────────────────────────


class GpuListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = Gpu
    template_name = "catalog/gpu_list.html"
    context_object_name = "gpus"
    datatable_columns = [
        {"key": "name", "label": "Nama VGA", "sortable": True, "searchable": True},
        {"key": "vga_type", "label": "Tipe", "sortable": True, "searchable": True},
        {"key": "actions", "label": "Aksi", "sortable": False, "searchable": False, "template": "catalog/_gpu_actions.html"},
    ]


class GpuCreateView(AdminRequiredMixin, CreateView):
    model = Gpu
    form_class = GpuForm
    template_name = "catalog/gpu_form.html"
    success_url = reverse_lazy("catalog:gpu_list")


class GpuUpdateView(AdminRequiredMixin, UpdateView):
    model = Gpu
    form_class = GpuForm
    template_name = "catalog/gpu_form.html"
    success_url = reverse_lazy("catalog:gpu_list")


class GpuDeleteView(AdminRequiredMixin, DeleteView):
    model = Gpu
    template_name = "catalog/gpu_confirm_delete.html"
    success_url = reverse_lazy("catalog:gpu_list")


# ─── SubBrand CRUD ───────────────────────────────────────────────────────────


class SubBrandListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = SubBrand
    template_name = "catalog/subbrand_list.html"
    context_object_name = "sub_brands"
    datatable_columns = [
        {"key": "name", "label": "Nama", "sortable": True, "searchable": True},
        {"key": "brand", "label": "Brand", "sortable": True, "searchable": True, "search_key": "brand__name", "sort_key": "brand__name"},
        {"key": "actions", "label": "Aksi", "sortable": False, "searchable": False, "template": "catalog/_subbrand_actions.html"},
    ]


class SubBrandCreateView(AdminRequiredMixin, CreateView):
    model = SubBrand
    form_class = SubBrandForm
    template_name = "catalog/subbrand_form.html"
    success_url = reverse_lazy("catalog:subbrand_list")


class SubBrandUpdateView(AdminRequiredMixin, UpdateView):
    model = SubBrand
    form_class = SubBrandForm
    template_name = "catalog/subbrand_form.html"
    success_url = reverse_lazy("catalog:subbrand_list")


class SubBrandDeleteView(AdminRequiredMixin, DeleteView):
    model = SubBrand
    template_name = "catalog/subbrand_confirm_delete.html"
    success_url = reverse_lazy("catalog:subbrand_list")


class ImportView(AdminRequiredMixin, View):
    template_name = "catalog/import.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        csv_file = request.FILES.get("csv_file")
        if not csv_file:
            messages.error(request, "Pilih file CSV terlebih dahulu.")
            return render(request, self.template_name)
        if not csv_file.name.lower().endswith(".csv"):
            messages.error(request, "File harus berformat .csv")
            return render(request, self.template_name)

        result = parse_and_validate(csv_file)
        serializable = [
            {k: str(v) if isinstance(v, Decimal) else v for k, v in row.items()}
            for row in result["valid_rows"]
        ]
        request.session["csv_import_rows"] = serializable
        return render(request, "catalog/_import_preview.html", {"result": result})


class ImportConfirmView(AdminRequiredMixin, View):
    def post(self, request):
        rows = request.session.pop("csv_import_rows", [])
        if not rows:
            messages.warning(request, "Tidak ada data untuk diimport. Upload ulang file CSV.")
            return redirect("catalog:import")

        created_laptops = []
        for row in rows:
            brand, _ = Brand.objects.get_or_create(name=row["brand"])
            processor, _ = Processor.objects.get_or_create(
                name=row["processor"],
                defaults={"tier": int(row["processor_tier"])},
            )
            vga, _ = Gpu.objects.get_or_create(
                name=row["vga"],
                defaults={"vga_type": row["vga_type"]},
            )
            created_laptops.append(Laptop(
                brand=brand,
                model=row["model"],
                processor=processor,
                ram_gb=int(row["ram_gb"]),
                storage_gb=int(row["storage_gb"]),
                storage_type=row["storage_type"],
                vga=vga,
                screen_inch=Decimal(str(row["screen_inch"])),
                battery_hours=Decimal(str(row["battery_hours"])),
                price_idr=int(row["price_idr"]),
            ))
        Laptop.objects.bulk_create(created_laptops)
        messages.success(request, f"{len(created_laptops)} laptop berhasil diimport.")
        return redirect("catalog:list")
