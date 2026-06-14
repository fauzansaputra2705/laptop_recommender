from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from accounts.mixins import AdminRequiredMixin

from .forms import LaptopForm
from .models import Laptop


class LaptopListView(AdminRequiredMixin, ListView):
    model = Laptop
    template_name = "catalog/list.html"
    context_object_name = "laptops"
    paginate_by = 25


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
