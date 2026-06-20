from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    # Laptop CRUD
    path("", views.LaptopListView.as_view(), name="list"),
    path("create/", views.LaptopCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.LaptopUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.LaptopDeleteView.as_view(), name="delete"),
    # Brand master
    path("brands/", views.BrandListView.as_view(), name="brand_list"),
    path("brands/create/", views.BrandCreateView.as_view(), name="brand_create"),
    path("brands/<int:pk>/edit/", views.BrandUpdateView.as_view(), name="brand_update"),
    path("brands/<int:pk>/delete/", views.BrandDeleteView.as_view(), name="brand_delete"),
    # Processor master
    path("processors/", views.ProcessorListView.as_view(), name="processor_list"),
    path("processors/create/", views.ProcessorCreateView.as_view(), name="processor_create"),
    path("processors/<int:pk>/edit/", views.ProcessorUpdateView.as_view(), name="processor_update"),
    path("processors/<int:pk>/delete/", views.ProcessorDeleteView.as_view(), name="processor_delete"),
    # Gpu master
    path("gpus/", views.GpuListView.as_view(), name="gpu_list"),
    path("gpus/create/", views.GpuCreateView.as_view(), name="gpu_create"),
    path("gpus/<int:pk>/edit/", views.GpuUpdateView.as_view(), name="gpu_update"),
    path("gpus/<int:pk>/delete/", views.GpuDeleteView.as_view(), name="gpu_delete"),
]
