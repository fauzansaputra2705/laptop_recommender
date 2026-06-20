from django.contrib.auth.models import User
from django.db import models

from catalog.models import Brand
from clustering.models import Cluster, ClusterModel


class Preference(models.Model):
    ROLE_CHOICES = [
        ("developer", "Developer"),
        ("designer", "UI/UX Designer"),
        ("business_analyst", "Business Analyst"),
        ("manajemen", "Staf Manajemen"),
    ]
    STORAGE_CHOICES = [("SSD", "SSD"), ("HDD", "HDD")]
    VGA_CHOICES = [("integrated", "Integrated"), ("dedicated", "Dedicated")]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="preferences"
    )
    role_target = models.CharField(max_length=20, choices=ROLE_CHOICES)
    budget_min_idr = models.BigIntegerField()
    budget_max_idr = models.BigIntegerField()
    min_ram_gb = models.PositiveIntegerField()
    min_processor_tier = models.PositiveSmallIntegerField()
    min_storage_gb = models.PositiveIntegerField()
    storage_type = models.CharField(max_length=3, choices=STORAGE_CHOICES, blank=True)
    vga_type = models.CharField(max_length=10, choices=VGA_CHOICES, blank=True)
    min_screen_inch = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    min_battery_hours = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    brand_preference = models.ForeignKey(
        Brand, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_role_target_display()} (Rp{self.budget_max_idr:,})"


class Recommendation(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recommendations"
    )
    preference = models.ForeignKey(
        Preference, on_delete=models.CASCADE, related_name="recommendations"
    )
    cluster_model = models.ForeignKey(ClusterModel, on_delete=models.CASCADE)
    selected_cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE)
    results = models.JSONField()
    precision_at_k = models.FloatField()
    k_value = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Rec #{self.pk} for {self.user.username} (P@K={self.precision_at_k:.2f})"
