from django.contrib import admin

from .models import Cluster, ClusterModel


class ClusterInline(admin.TabularInline):
    model = Cluster
    extra = 0
    readonly_fields = ("label", "interpretation", "member_count")


@admin.register(ClusterModel)
class ClusterModelAdmin(admin.ModelAdmin):
    list_display = ("pk", "k_optimal", "silhouette_score", "is_active", "created_at")
    list_filter = ("is_active",)
    inlines = [ClusterInline]


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ("label", "cluster_model", "interpretation", "member_count")
    list_filter = ("cluster_model",)
