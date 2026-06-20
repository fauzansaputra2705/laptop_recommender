import random

import pytest

from catalog.models import Brand, Gpu, Laptop, Processor

_BRANDS = ["ASUS", "Lenovo", "HP", "Acer", "Dell", "MSI", "Apple"]

_PROCESSORS = [
    ("Intel Core i3-1115G4", 3),
    ("Intel Core i5-1235U", 5),
    ("Intel Core i7-13700H", 7),
    ("Intel Core i9-13900H", 9),
    ("AMD Ryzen 3 7320U", 3),
    ("AMD Ryzen 5 7530U", 5),
    ("AMD Ryzen 7 7840HS", 7),
    ("AMD Ryzen 9 7940HS", 9),
    ("Apple M2", 8),
    ("Apple M3 Pro", 9),
]

_INTEGRATED_VGA = ["Intel Iris Xe", "AMD Radeon Graphics", "Apple GPU"]
_DEDICATED_VGA = ["NVIDIA GeForce RTX 3050", "NVIDIA GeForce RTX 4060", "NVIDIA GeForce RTX 4070"]


def _seed_masters():
    brands = {}
    for name in _BRANDS:
        obj, _ = Brand.objects.get_or_create(name=name)
        brands[name] = obj

    processors = {}
    for name, tier in _PROCESSORS:
        obj, _ = Processor.objects.get_or_create(name=name, defaults={"tier": tier})
        processors[name] = obj

    gpus = {}
    for name in _INTEGRATED_VGA + _DEDICATED_VGA:
        vga_type = "dedicated" if name in _DEDICATED_VGA else "integrated"
        obj, _ = Gpu.objects.get_or_create(name=name, defaults={"vga_type": vga_type})
        gpus[name] = obj

    return brands, processors, gpus


@pytest.fixture
def make_laptops(db):
    """Factory fixture — call make_laptops(n) to create n test laptops."""
    brands, processors, gpus = _seed_masters()
    proc_tiers = dict(_PROCESSORS)  # name -> tier

    def _make(n, seed=1):
        rng = random.Random(seed)
        laptops = []
        for _ in range(n):
            brand_name = rng.choice(_BRANDS)
            candidates = [
                p for p in _PROCESSORS
                if (brand_name == "Apple") == p[0].startswith("Apple")
            ] or _PROCESSORS
            proc_name, tier = rng.choice(candidates)
            if tier <= 3:
                ram = rng.choice([4, 8, 8, 16])
                storage = rng.choice([256, 512])
            elif tier <= 5:
                ram = rng.choice([8, 16, 16])
                storage = rng.choice([512, 1024])
            elif tier <= 7:
                ram = rng.choice([16, 16, 32])
                storage = rng.choice([512, 1024])
            else:
                ram = rng.choice([16, 32, 32, 64])
                storage = rng.choice([1024, 2048])

            if brand_name == "Apple":
                vga_name = rng.choice(_INTEGRATED_VGA)
            else:
                vga_name = rng.choice(_DEDICATED_VGA) if rng.random() < 0.4 else rng.choice(_INTEGRATED_VGA)

            base = 2_500_000 + tier * 1_350_000 + ram * 90_000 + storage * 2_200
            if vga_name in _DEDICATED_VGA:
                base += 4_500_000
            if brand_name in ("Apple", "MSI", "Dell"):
                base *= 1.18
            price = int(max(3_000_000, min(60_000_000, base * rng.uniform(0.9, 1.1))))

            laptops.append(Laptop(
                brand=brands[brand_name],
                model=f"{brand_name} TestModel {rng.randint(100, 999)}",
                processor=processors[proc_name],
                ram_gb=ram,
                storage_gb=storage,
                storage_type="SSD",
                vga=gpus[vga_name],
                screen_inch=rng.choice([13.3, 14.0, 15.6, 16.0, 17.3]),
                battery_hours=round(rng.uniform(5.0, 15.0), 1),
                price_idr=price,
            ))
        Laptop.objects.bulk_create(laptops)
        return laptops

    return _make
