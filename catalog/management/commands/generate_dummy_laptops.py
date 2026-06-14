import random

from django.core.management.base import BaseCommand

from catalog.models import Laptop

BRANDS = ["ASUS", "Lenovo", "HP", "Acer", "Dell", "MSI", "Apple"]

# (processor name, ordinal tier 1-10)
PROCESSORS = [
    ("Intel Core i3-1115G4", 3),
    ("Intel Core i3-1215U", 3),
    ("Intel Core i5-1235U", 5),
    ("Intel Core i5-13420H", 5),
    ("Intel Core i7-1255U", 6),
    ("Intel Core i7-13700H", 7),
    ("Intel Core i9-13900H", 9),
    ("AMD Ryzen 3 7320U", 3),
    ("AMD Ryzen 5 5600H", 5),
    ("AMD Ryzen 5 7530U", 5),
    ("AMD Ryzen 7 7840HS", 7),
    ("AMD Ryzen 9 7940HS", 9),
    ("Apple M2", 8),
    ("Apple M3 Pro", 9),
]

RAM_OPTIONS = [4, 8, 16, 32, 64]
STORAGE_OPTIONS = [256, 512, 1024, 2048]
SCREEN_OPTIONS = [13.3, 14.0, 15.6, 16.0, 17.3]

INTEGRATED_VGA = ["Intel UHD Graphics", "Intel Iris Xe", "AMD Radeon Graphics", "Apple GPU"]
DEDICATED_VGA = [
    "NVIDIA GeForce RTX 3050",
    "NVIDIA GeForce RTX 4060",
    "NVIDIA GeForce RTX 4070",
    "AMD Radeon RX 6600M",
]

MIN_PRICE = 3_000_000
MAX_PRICE = 60_000_000


class Command(BaseCommand):
    help = "Generate realistic dummy laptop records (Indonesian market pricing)."

    def add_arguments(self, parser):
        parser.add_argument("--count", type=int, default=300)
        parser.add_argument("--clear", action="store_true", help="Delete existing laptops first")
        parser.add_argument("--seed", type=int, default=None)

    def handle(self, *args, **options):
        count = options["count"]
        seed = options["seed"]
        if seed is not None:
            random.seed(seed)

        if options["clear"]:
            deleted, _ = Laptop.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Cleared existing laptops ({deleted})."))

        laptops = []
        for _ in range(count):
            brand = random.choice(BRANDS)
            # Apple uses Apple silicon only
            if brand == "Apple":
                proc, tier = random.choice([p for p in PROCESSORS if p[0].startswith("Apple")])
            else:
                proc, tier = random.choice([p for p in PROCESSORS if not p[0].startswith("Apple")])

            ram = random.choice(RAM_OPTIONS)
            storage = random.choice(STORAGE_OPTIONS)
            storage_type = "SSD" if random.random() < 0.9 else "HDD"

            # dedicated VGA more likely on high tiers; Apple stays integrated
            if brand == "Apple":
                vga_type = "integrated"
            else:
                dedicated_prob = 0.15 + (tier / 10) * 0.5
                vga_type = "dedicated" if random.random() < dedicated_prob else "integrated"
            vga = random.choice(DEDICATED_VGA if vga_type == "dedicated" else INTEGRATED_VGA)

            screen = random.choice(SCREEN_OPTIONS)
            battery = round(random.uniform(4.0, 18.0), 1)

            # price model: base scales with tier, ram, storage, dedicated vga, brand premium
            base = 2_500_000
            base += tier * 1_350_000
            base += ram * 90_000
            base += storage * 2_200
            if vga_type == "dedicated":
                base += 4_500_000
            if brand in ("Apple", "MSI", "Dell"):
                base *= 1.18
            jitter = random.uniform(0.9, 1.1)
            price = int(max(MIN_PRICE, min(MAX_PRICE, base * jitter)))

            model = self._model_name(brand, tier, vga_type)
            laptops.append(
                Laptop(
                    brand=brand,
                    model=model,
                    processor=proc,
                    processor_tier=tier,
                    ram_gb=ram,
                    storage_gb=storage,
                    storage_type=storage_type,
                    vga=vga,
                    vga_type=vga_type,
                    screen_inch=screen,
                    battery_hours=battery,
                    price_idr=price,
                )
            )

        Laptop.objects.bulk_create(laptops)
        self.stdout.write(self.style.SUCCESS(f"Created {len(laptops)} dummy laptops."))

    def _model_name(self, brand, tier, vga_type):
        series = {
            "ASUS": ["VivoBook", "ZenBook", "ROG Strix", "TUF Gaming"],
            "Lenovo": ["IdeaPad", "ThinkPad", "Legion", "Yoga"],
            "HP": ["Pavilion", "Envy", "Omen", "ProBook"],
            "Acer": ["Aspire", "Swift", "Predator", "Nitro"],
            "Dell": ["Inspiron", "XPS", "Latitude", "Alienware"],
            "MSI": ["Modern", "Prestige", "Katana", "Stealth"],
            "Apple": ["MacBook Air", "MacBook Pro"],
        }
        name = random.choice(series[brand])
        suffix = random.choice(["14", "15", "16", "Pro 14", "Plus", "X", str(random.randint(100, 999))])
        return f"{name} {suffix}"
