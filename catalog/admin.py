from django.contrib import admin

from .models import Brand, Gpu, Laptop, Processor


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Processor)
class ProcessorAdmin(admin.ModelAdmin):
    list_display = ("name", "tier")
    list_filter = ("tier",)
    search_fields = ("name",)


@admin.register(Gpu)
class GpuAdmin(admin.ModelAdmin):
    list_display = ("name", "vga_type")
    list_filter = ("vga_type",)
    search_fields = ("name",)


@admin.register(Laptop)
class LaptopAdmin(admin.ModelAdmin):
    list_display = (
        "brand",
        "model",
        "processor",
        "ram_gb",
        "price_idr",
        "cluster_label",
    )
    list_filter = ("brand", "storage_type", "vga__vga_type")
    search_fields = ("brand__name", "model", "processor__name")
