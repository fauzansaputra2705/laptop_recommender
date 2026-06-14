from django import forms

from .models import Laptop

INPUT = "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800"


class LaptopForm(forms.ModelForm):
    class Meta:
        model = Laptop
        fields = [
            "brand", "model", "processor", "processor_tier", "ram_gb",
            "storage_gb", "storage_type", "vga", "vga_type", "screen_inch",
            "battery_hours", "price_idr",
        ]
        widgets = {
            "brand": forms.TextInput(attrs={"class": INPUT}),
            "model": forms.TextInput(attrs={"class": INPUT}),
            "processor": forms.TextInput(attrs={"class": INPUT}),
            "processor_tier": forms.NumberInput(attrs={"class": INPUT, "min": 1, "max": 10}),
            "ram_gb": forms.NumberInput(attrs={"class": INPUT}),
            "storage_gb": forms.NumberInput(attrs={"class": INPUT}),
            "storage_type": forms.Select(attrs={"class": INPUT}),
            "vga": forms.TextInput(attrs={"class": INPUT}),
            "vga_type": forms.Select(attrs={"class": INPUT}),
            "screen_inch": forms.NumberInput(attrs={"class": INPUT, "step": "0.1"}),
            "battery_hours": forms.NumberInput(attrs={"class": INPUT, "step": "0.1"}),
            "price_idr": forms.NumberInput(attrs={"class": INPUT}),
        }
