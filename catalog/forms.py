from django import forms

from .models import Brand, Gpu, Laptop, Processor, SubBrand

INPUT = "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800"


class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ["name"]
        widgets = {"name": forms.TextInput(attrs={"class": INPUT})}


class SubBrandForm(forms.ModelForm):
    class Meta:
        model = SubBrand
        fields = ["name", "brand"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT}),
            "brand": forms.Select(attrs={"class": INPUT}),
        }


class ProcessorForm(forms.ModelForm):
    class Meta:
        model = Processor
        fields = ["name", "tier"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT}),
            "tier": forms.NumberInput(attrs={"class": INPUT, "min": 1, "max": 10}),
        }


class GpuForm(forms.ModelForm):
    class Meta:
        model = Gpu
        fields = ["name", "vga_type"]
        widgets = {
            "name": forms.TextInput(attrs={"class": INPUT}),
            "vga_type": forms.Select(attrs={"class": INPUT}),
        }


class LaptopForm(forms.ModelForm):
    class Meta:
        model = Laptop
        fields = [
            "brand", "sub_brand", "model", "processor", "ram_gb",
            "storage_gb", "storage_type", "vga", "screen_inch",
            "battery_hours", "price_idr",
        ]
        widgets = {
            "brand": forms.Select(attrs={"class": INPUT}),
            "sub_brand": forms.Select(attrs={"class": INPUT}),
            "model": forms.TextInput(attrs={"class": INPUT}),
            "processor": forms.Select(attrs={"class": INPUT}),
            "ram_gb": forms.NumberInput(attrs={"class": INPUT}),
            "storage_gb": forms.NumberInput(attrs={"class": INPUT}),
            "storage_type": forms.Select(attrs={"class": INPUT}),
            "vga": forms.Select(attrs={"class": INPUT}),
            "screen_inch": forms.NumberInput(attrs={"class": INPUT, "step": "0.1"}),
            "battery_hours": forms.NumberInput(attrs={"class": INPUT, "step": "0.1"}),
            "price_idr": forms.NumberInput(attrs={"class": INPUT}),
        }
