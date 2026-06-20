import pytest
from django.contrib.auth.models import User
from django.urls import reverse


@pytest.mark.django_db
def test_landing_accessible_anonymously(client):
    assert client.get(reverse("core:landing")).status_code == 200


@pytest.mark.django_db
def test_dashboard_requires_login(client):
    resp = client.get(reverse("core:dashboard"))
    assert resp.status_code in (301, 302)


@pytest.mark.django_db
def test_admin_sees_admin_links(client):
    user = User.objects.create_user("a", email="a@example.com", password="x")
    user.profile.role = "admin"
    user.profile.save()
    client.force_login(user)
    resp = client.get(reverse("core:dashboard"))
    content = resp.content.lower()
    assert b"clustering" in content or b"training" in content


@pytest.mark.django_db
def test_user_does_not_see_admin_links(client):
    user = User.objects.create_user("u", email="u@example.com", password="x")
    client.force_login(user)
    resp = client.get(reverse("core:dashboard"))
    assert b"Kelola Katalog" not in resp.content


# --- Analytics chart tests ---

@pytest.mark.django_db
def test_dashboard_admin_no_data(client):
    user = User.objects.create_user("a2", email="a2@example.com", password="x")
    user.profile.role = "admin"
    user.profile.save()
    client.force_login(user)
    resp = client.get(reverse("core:dashboard"))
    assert resp.status_code == 200
    assert resp.context["chart_role"] is None
    assert resp.context["chart_cluster"] is None


@pytest.mark.django_db
def test_dashboard_admin_has_charts(client, make_laptops):
    from clustering.services import run_training
    from django.test import Client as DjangoClient

    # create admin
    admin = User.objects.create_user("admin_chart", email="admin_chart@example.com", password="x")
    admin.profile.role = "admin"
    admin.profile.save()

    # create user + recommendation
    user = User.objects.create_user("user_chart", email="user_chart@example.com", password="x")
    make_laptops(80, seed=20)
    run_training()
    user_client = DjangoClient()
    user_client.force_login(user)
    user_client.post(reverse("recommender:recommend"), {
        "role_target": "developer", "budget_min_idr": 8000000,
        "budget_max_idr": 25000000, "min_ram_gb": 8,
        "min_processor_tier": 3, "min_storage_gb": 256, "top_n": 5,
    })

    client.force_login(admin)
    resp = client.get(reverse("core:dashboard"))
    assert resp.status_code == 200
    assert resp.context["chart_role"] is not None
    assert resp.context["chart_cluster"] is not None


@pytest.mark.django_db
def test_dashboard_user_no_charts(client):
    user = User.objects.create_user("u_chart", email="u_chart@example.com", password="x")
    client.force_login(user)
    resp = client.get(reverse("core:dashboard"))
    assert resp.status_code == 200
    assert "chart_role" not in resp.context
