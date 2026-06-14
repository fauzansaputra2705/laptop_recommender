import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from django.urls import reverse


def _admin(client):
    u = User.objects.create_user("a", email="a@example.com", password="x")
    u.profile.role = "admin"
    u.profile.save()
    client.force_login(u)
    return u


@pytest.mark.django_db
def test_user_forbidden_from_clustering(client):
    u = User.objects.create_user("u", email="u@example.com", password="x")
    client.force_login(u)
    assert client.get(reverse("clustering:dashboard")).status_code == 403


@pytest.mark.django_db
def test_train_insufficient_data_returns_error_partial(client):
    _admin(client)
    call_command("generate_dummy_laptops", "--count", "5", "--seed", "9")
    resp = client.post(reverse("clustering:train"), HTTP_HX_REQUEST="true")
    assert resp.status_code == 200
    assert b"minimal" in resp.content.lower()


@pytest.mark.django_db
def test_train_success_returns_result_partial(client):
    _admin(client)
    call_command("generate_dummy_laptops", "--count", "60", "--seed", "9")
    resp = client.post(reverse("clustering:train"), HTTP_HX_REQUEST="true")
    assert resp.status_code == 200
    assert b"ilhouette" in resp.content


@pytest.mark.django_db
def test_dashboard_renders_for_admin(client):
    _admin(client)
    assert client.get(reverse("clustering:dashboard")).status_code == 200
