from django.contrib import admin

from .models import Preference, Recommendation


@admin.register(Preference)
class PreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "role_target", "budget_min_idr", "budget_max_idr", "min_ram_gb", "created_at")
    list_filter = ("role_target",)
    search_fields = ("user__username", "user__email")


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ("pk", "user", "selected_cluster", "precision_at_k", "k_value", "created_at")
    list_filter = ("selected_cluster",)
    search_fields = ("user__username",)
