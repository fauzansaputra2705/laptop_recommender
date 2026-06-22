from django.db import models


class Brand(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SubBrand(models.Model):
    name = models.CharField(max_length=50)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="sub_brands")

    class Meta:
        ordering = ["brand", "name"]
        unique_together = [("brand", "name")]
        verbose_name = "Sub Brand"
        verbose_name_plural = "Sub Brands"

    def __str__(self):
        return f"{self.brand.name} - {self.name}"


class Processor(models.Model):
    name = models.CharField(max_length=120, unique=True)
    tier = models.PositiveSmallIntegerField(help_text="Ordinal performance tier 1-10")

    class Meta:
        ordering = ["-tier", "name"]

    def __str__(self):
        return self.name


class Gpu(models.Model):
    VGA_CHOICES = [("integrated", "Integrated"), ("dedicated", "Dedicated")]

    name = models.CharField(max_length=80, unique=True)
    vga_type = models.CharField(
        max_length=10, choices=VGA_CHOICES, default="integrated"
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Laptop(models.Model):
    STORAGE_CHOICES = [("SSD", "SSD"), ("HDD", "HDD")]

    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="laptops")
    sub_brand = models.ForeignKey(
        SubBrand,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="laptops",
    )
    model = models.CharField(max_length=120)
    processor = models.ForeignKey(
        Processor, on_delete=models.PROTECT, related_name="laptops"
    )
    ram_gb = models.PositiveIntegerField()
    storage_gb = models.PositiveIntegerField()
    storage_type = models.CharField(
        max_length=3, choices=STORAGE_CHOICES, default="SSD"
    )
    vga = models.ForeignKey(Gpu, on_delete=models.PROTECT, related_name="laptops")
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
