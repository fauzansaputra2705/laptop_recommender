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
            "min_processor_tier": 5, "min_storage_gb": 512, "top_n": 5,
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
            "min_processor_tier": 3, "min_storage_gb": 256, "top_n": 5,
        },
        HTTP_HX_REQUEST="true",
    )
    assert resp.status_code == 200
    assert b"cluster" in resp.content.lower() or b"admin" in resp.content.lower()


@pytest.mark.django_db
def test_recommend_post_top_n_3(user_client, make_laptops):
    client, user = user_client
    make_laptops(80, seed=5)
    run_training()
    resp = client.post(reverse("recommender:recommend"), {
        "role_target": "developer", "budget_min_idr": 8000000,
        "budget_max_idr": 25000000, "min_ram_gb": 16,
        "min_processor_tier": 5, "min_storage_gb": 512,
        "top_n": 3,
    }, HTTP_HX_REQUEST="true")
    assert resp.status_code == 200
    from recommender.models import Recommendation
    rec = Recommendation.objects.filter(user=user).first()
    assert rec.k_value == 3


@pytest.mark.django_db
def test_result_detail_owner_ok(user_client, make_laptops):
    from clustering.services import run_training
    from recommender.models import Recommendation
    client, user = user_client
    make_laptops(80, seed=6)
    run_training()
    client.post(reverse("recommender:recommend"), {
        "role_target": "developer", "budget_min_idr": 8000000,
        "budget_max_idr": 25000000, "min_ram_gb": 16,
        "min_processor_tier": 5, "min_storage_gb": 512,
        "top_n": 5,
    }, HTTP_HX_REQUEST="true")
    rec = Recommendation.objects.filter(user=user).first()
    resp = client.get(reverse("recommender:result", args=[rec.pk]))
    assert resp.status_code == 200


@pytest.mark.django_db
def test_result_detail_other_user_404(user_client, make_laptops):
    from clustering.services import run_training
    from recommender.models import Recommendation
    client, user = user_client
    make_laptops(80, seed=7)
    run_training()
    client.post(reverse("recommender:recommend"), {
        "role_target": "developer", "budget_min_idr": 8000000,
        "budget_max_idr": 25000000, "min_ram_gb": 16,
        "min_processor_tier": 5, "min_storage_gb": 512,
        "top_n": 5,
    }, HTTP_HX_REQUEST="true")
    rec = Recommendation.objects.filter(user=user).first()
    # different user
    from django.contrib.auth.models import User
    other = User.objects.create_user("other2", email="other2@example.com", password="x")
    client.force_login(other)
    resp = client.get(reverse("recommender:result", args=[rec.pk]))
    assert resp.status_code == 404


# --- CompareView tests ---

def _make_rec(client, user, make_laptops, seed=10):
    from recommender.models import Recommendation
    make_laptops(80, seed=seed)
    run_training()
    client.post(reverse("recommender:recommend"), {
        "role_target": "developer", "budget_min_idr": 8000000,
        "budget_max_idr": 25000000, "min_ram_gb": 8,
        "min_processor_tier": 3, "min_storage_gb": 256, "top_n": 5,
    }, HTTP_HX_REQUEST="true")
    return Recommendation.objects.filter(user=user).first()


@pytest.mark.django_db
def test_compare_view_valid(user_client, make_laptops):
    client, user = user_client
    rec = _make_rec(client, user, make_laptops, seed=10)
    ids = [r["id"] for r in rec.results[:2]]
    resp = client.get(reverse("recommender:compare"), {"ids": ",".join(str(i) for i in ids)})
    assert resp.status_code == 200
    assert b"Perbandingan" in resp.content


@pytest.mark.django_db
def test_compare_view_no_ids(user_client, make_laptops):
    client, user = user_client
    _make_rec(client, user, make_laptops, seed=11)
    resp = client.get(reverse("recommender:compare"))
    assert resp.status_code == 400


@pytest.mark.django_db
def test_compare_view_other_user_ids(user_client, make_laptops):
    from recommender.models import Recommendation
    client, user = user_client
    rec = _make_rec(client, user, make_laptops, seed=12)
    ids = [r["id"] for r in rec.results[:2]]
    # login as different user
    other = User.objects.create_user("other_cmp", email="other_cmp@example.com", password="x")
    client.force_login(other)
    resp = client.get(reverse("recommender:compare"), {"ids": ",".join(str(i) for i in ids)})
    assert resp.status_code == 400


@pytest.mark.django_db
def test_compare_view_max_3(user_client, make_laptops):
    client, user = user_client
    rec = _make_rec(client, user, make_laptops, seed=13)
    ids = [r["id"] for r in rec.results]  # up to 5
    resp = client.get(reverse("recommender:compare"), {"ids": ",".join(str(i) for i in ids)})
    # should succeed with first 3
    assert resp.status_code == 200
