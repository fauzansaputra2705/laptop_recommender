import pytest
from django.core.management import call_command

from catalog.models import Laptop


@pytest.mark.django_db
def test_generator_creates_realistic_laptops():
    call_command("generate_dummy_laptops", "--count", "50")
    assert Laptop.objects.count() == 50
    for lap in Laptop.objects.all():
        assert 1 <= lap.processor_tier <= 10
        assert lap.ram_gb in (4, 8, 16, 32, 64)
        assert 3_000_000 <= lap.price_idr <= 60_000_000
        assert 11.0 <= float(lap.screen_inch) <= 17.3


@pytest.mark.django_db
def test_generator_clear_flag_resets():
    call_command("generate_dummy_laptops", "--count", "10", "--seed", "1")
    call_command("generate_dummy_laptops", "--count", "10", "--seed", "1", "--clear")
    assert Laptop.objects.count() == 10
