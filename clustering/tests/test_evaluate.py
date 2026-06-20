import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from clustering.models import ClusterModel
from clustering.plots import comparison_bar_png


def test_comparison_bar_png_returns_nonempty_string():
    result = comparison_bar_png(["#1", "#2", "#3"], [0.4, 0.6, 0.55], active_idx=1)
    assert isinstance(result, str)
    assert len(result) > 100


def test_comparison_bar_png_empty():
    result = comparison_bar_png([], [], active_idx=None)
    assert isinstance(result, str)


@pytest.mark.django_db
def test_evaluate_view_admin_ok(client):
    u = User.objects.create_user("adm", email="adm@example.com", password="x")
    u.profile.role = "admin"
    u.profile.save()
    client.force_login(u)
    resp = client.get(reverse("clustering:evaluate"))
    assert resp.status_code == 200
    assert b"Evaluasi" in resp.content


@pytest.mark.django_db
def test_evaluate_view_user_forbidden(client):
    u = User.objects.create_user("usr", email="usr@example.com", password="x")
    client.force_login(u)
    resp = client.get(reverse("clustering:evaluate"))
    assert resp.status_code == 403
