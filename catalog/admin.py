from django.contrib import admin

from .models import Laptop


@admin.register(Laptop)
class LaptopAdmin(admin.ModelAdmin):
    list_display = (
        "brand",
        "model",
        "processor_tier",
        "ram_gb",
        "price_idr",
        "cluster_label",
    )
    list_filter = ("brand", "storage_type", "vga_type")
    search_fields = ("brand", "model")
