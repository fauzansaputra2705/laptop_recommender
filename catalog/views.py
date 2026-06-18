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
