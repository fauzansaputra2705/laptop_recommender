from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.mixins import AdminRequiredMixin
from datatable.mixins import DatatableViewMixin

from .forms import BrandForm, GpuForm, LaptopForm, ProcessorForm
from .models import Brand, Gpu, Laptop, Processor


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
