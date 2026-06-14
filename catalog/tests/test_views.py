import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from catalog.models import Laptop


def _admin(client):
    u = User.objects.create_user("a", email="a@example.com", password="x")
    u.profile.role = "admin"
    u.profile.save()
    client.force_login(u)
    return u


def _user(client):
    u = User.objects.create_user("u", email="u@example.com", password="x")
    client.force_login(u)
    return u


@pytest.mark.django_db
def test_user_forbidden_from_catalog(client):
    _user(client)
    assert client.get(reverse("catalog:list")).status_code == 403


@pytest.mark.django_db
def test_admin_can_list_and_create(client):
    _admin(client)
    assert client.get(reverse("catalog:list")).status_code == 200
    client.post(
        reverse("catalog:create"),
        {
            "brand": "ASUS", "model": "X", "processor": "i5",
            "processor_tier": 5, "ram_gb": 16, "storage_gb": 512,
            "storage_type": "SSD", "vga": "Iris", "vga_type": "integrated",
            "screen_inch": 14.0, "battery_hours": 8.0, "price_idr": 9500000,
        },
    )
    assert Laptop.objects.filter(brand="ASUS", model="X").exists()
