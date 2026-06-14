from django.db import models


class Laptop(models.Model):
    STORAGE_CHOICES = [("SSD", "SSD"), ("HDD", "HDD")]
    VGA_CHOICES = [("integrated", "Integrated"), ("dedicated", "Dedicated")]

    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=120)
    processor = models.CharField(max_length=120)
    processor_tier = models.PositiveSmallIntegerField(
        help_text="Ordinal performance tier 1-10"
    )
    ram_gb = models.PositiveIntegerField()
    storage_gb = models.PositiveIntegerField()
    storage_type = models.CharField(
        max_length=3, choices=STORAGE_CHOICES, default="SSD"
    )
    vga = models.CharField(max_length=80)
    vga_type = models.CharField(
        max_length=10, choices=VGA_CHOICES, default="integrated"
    )
    screen_inch = models.DecimalField(max_digits=4, decimal_places=1)
    battery_hours = models.DecimalField(max_digits=4, decimal_places=1)
    price_idr = models.BigIntegerField()
    cluster_label = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["brand", "model"]

    def __str__(self):
        return f"{self.brand} {self.model}"
