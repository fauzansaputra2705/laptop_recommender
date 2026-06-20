from django import forms

from catalog.models import Brand
from .models import Preference

INPUT = "w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 dark:border-slate-600 dark:bg-slate-800"


class PreferenceForm(forms.ModelForm):
    class Meta:
        model = Preference
        fields = [
            "role_target",
            "budget_min_idr",
            "budget_max_idr",
            "min_ram_gb",
            "min_processor_tier",
            "min_storage_gb",
            "storage_type",
            "vga_type",
            "min_screen_inch",
            "min_battery_hours",
            "brand_preference",
        ]
        widgets = {
            "role_target": forms.Select(attrs={"class": INPUT}),
            "budget_min_idr": forms.NumberInput(attrs={"class": INPUT, "inputmode": "numeric"}),
            "budget_max_idr": forms.NumberInput(attrs={"class": INPUT, "inputmode": "numeric"}),
            "min_ram_gb": forms.NumberInput(attrs={"class": INPUT, "inputmode": "numeric"}),
            "min_processor_tier": forms.NumberInput(attrs={"class": INPUT, "inputmode": "numeric", "min": 1, "max": 10}),
            "min_storage_gb": forms.NumberInput(attrs={"class": INPUT, "inputmode": "numeric"}),
            "storage_type": forms.Select(attrs={"class": INPUT}),
            "vga_type": forms.Select(attrs={"class": INPUT}),
            "min_screen_inch": forms.NumberInput(attrs={"class": INPUT, "step": "0.1"}),
            "min_battery_hours": forms.NumberInput(attrs={"class": INPUT, "step": "0.1"}),
            "brand_preference": forms.Select(attrs={"class": INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["brand_preference"].empty_label = "Semua merek"
