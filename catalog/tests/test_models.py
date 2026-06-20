import pytest

from catalog.models import Brand, Gpu, Laptop, Processor


@pytest.mark.django_db
def test_laptop_str_and_fields():
    brand = Brand.objects.create(name="ASUS")
    proc = Processor.objects.create(name="Intel Core i5-1235U", tier=5)
    gpu = Gpu.objects.create(name="Intel Iris Xe", vga_type="integrated")
    lap = Laptop.objects.create(
        brand=brand,
        model="VivoBook 14",
        processor=proc,
        ram_gb=16,
        storage_gb=512,
        storage_type="SSD",
        vga=gpu,
        screen_inch=14.0,
        battery_hours=8.0,
        price_idr=9500000,
    )
    assert str(lap) == "ASUS VivoBook 14"
    assert lap.cluster_label is None
