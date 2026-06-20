import pytest
from django.contrib.auth.models import User
from django.urls import reverse

from clustering.services import run_training


@pytest.fixture
def user_client(client, db):
    user = User.objects.create_user("u", email="u@example.com", password="x")
    client.force_login(user)
    return client, user


@pytest.mark.django_db
def test_recommend_get_renders_form(user_client):
    client, _ = user_client
    resp = client.get(reverse("recommender:recommend"))
    assert resp.status_code == 200
    assert b"role_target" in resp.content


@pytest.mark.django_db
def test_recommend_post_returns_results_partial(user_client, make_laptops):
    client, _ = user_client
    make_laptops(80, seed=5)
    run_training()
    resp = client.post(
        reverse("recommender:recommend"),
        {
            "role_target": "developer", "budget_min_idr": 8000000,
            "budget_max_idr": 25000000, "min_ram_gb": 16,
            "min_processor_tier": 5, "min_storage_gb": 512,
        },
        HTTP_HX_REQUEST="true",
    )
    assert resp.status_code == 200
    assert b"recision" in resp.content  # Precision / precision


@pytest.mark.django_db
def test_recommend_without_active_model_shows_message(user_client):
    client, _ = user_client
    resp = client.post(
        reverse("recommender:recommend"),
        {
            "role_target": "manajemen", "budget_min_idr": 5000000,
            "budget_max_idr": 12000000, "min_ram_gb": 8,
            "min_processor_tier": 3, "min_storage_gb": 256,
        },
        HTTP_HX_REQUEST="true",
    )
    assert resp.status_code == 200
    assert b"training" in resp.content.lower()
