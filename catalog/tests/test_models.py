import pytest

from catalog.models import Laptop


@pytest.mark.django_db
def test_laptop_str_and_fields():
    lap = Laptop.objects.create(
        brand="ASUS",
        model="VivoBook 14",
        processor="Intel Core i5-1235U",
        processor_tier=5,
        ram_gb=16,
        storage_gb=512,
        storage_type="SSD",
        vga="Intel Iris Xe",
        vga_type="integrated",
        screen_inch=14.0,
        battery_hours=8.0,
        price_idr=9500000,
    )
    assert str(lap) == "ASUS VivoBook 14"
    assert lap.cluster_label is None
