import io
import pytest
from django.contrib.auth.models import User
from django.urls import reverse

VALID_CSV = b"""brand,model,processor,processor_tier,ram_gb,storage_gb,storage_type,vga,vga_type,screen_inch,battery_hours,price_idr
ASUS,VivoBook 14,Intel Core i5,5,16,512,SSD,Intel Iris Xe,integrated,14.0,8.0,12000000
"""


def _admin(client):
    u = User.objects.create_user("adm", email="adm@example.com", password="x")
    u.profile.role = "admin"
    u.profile.save()
    client.force_login(u)
    return u


@pytest.mark.django_db
def test_import_get_admin_ok(client):
    _admin(client)
    resp = client.get(reverse("catalog:import"))
    assert resp.status_code == 200
    assert b"CSV" in resp.content


@pytest.mark.django_db
def test_import_get_user_forbidden(client):
    u = User.objects.create_user("usr", email="usr@example.com", password="x")
    client.force_login(u)
    resp = client.get(reverse("catalog:import"))
    assert resp.status_code == 403


@pytest.mark.django_db
def test_import_post_valid_csv_shows_preview(client):
    _admin(client)
    f = io.BytesIO(VALID_CSV)
    f.name = "laptops.csv"
    resp = client.post(reverse("catalog:import"), {"csv_file": f})
    assert resp.status_code == 200
    assert b"valid" in resp.content.lower() or b"konfirmasi" in resp.content.lower()


@pytest.mark.django_db
def test_import_confirm_creates_laptops(client):
    from catalog.models import Laptop
    _admin(client)
    # prime the session via upload
    f = io.BytesIO(VALID_CSV)
    f.name = "laptops.csv"
    client.post(reverse("catalog:import"), {"csv_file": f})
    count_before = Laptop.objects.count()
    resp = client.post(reverse("catalog:import_confirm"))
    assert resp.status_code == 302
    assert Laptop.objects.count() == count_before + 1
