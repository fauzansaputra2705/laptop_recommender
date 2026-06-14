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
