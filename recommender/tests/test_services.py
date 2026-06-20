import pytest
from django.contrib.auth.models import User

from clustering.services import run_training
from recommender.models import Preference, Recommendation
from recommender.services import NoActiveModel, _routing_record, generate_recommendation


@pytest.mark.django_db
def test_routing_record_floors_specs_at_role_target():
    # User minimums are below the developer target; routing vector must be
    # lifted to the target floor so it doesn't route to a cheaper cluster.
    user = User.objects.create_user("rt", email="rt@example.com", password="x")
    pref = Preference.objects.create(
        user=user, role_target="developer", budget_min_idr=10000000,
        budget_max_idr=30000000, min_ram_gb=8, min_processor_tier=3,
        min_storage_gb=256,
    )
    rec = _routing_record(pref)
    # developer target: tier 7, ram 16, storage 1024
    assert rec["processor_tier"] == 7
    assert rec["ram_gb"] == 16
    assert rec["storage_gb"] == 1024
    # price uses budget midpoint, not the max
    assert rec["price_idr"] == 20000000


@pytest.mark.django_db
def test_routing_record_keeps_user_specs_above_target():
    # When the user asks for more than the target, keep the higher value.
    user = User.objects.create_user("rt2", email="rt2@example.com", password="x")
    pref = Preference.objects.create(
        user=user, role_target="manajemen", budget_min_idr=8000000,
        budget_max_idr=12000000, min_ram_gb=32, min_processor_tier=8,
        min_storage_gb=2048,
    )
    rec = _routing_record(pref)
    assert rec["processor_tier"] == 8
    assert rec["ram_gb"] == 32
    assert rec["storage_gb"] == 2048


@pytest.mark.django_db
def test_generate_recommendation_end_to_end(make_laptops):
    make_laptops(80, seed=3)
    run_training()
    user = User.objects.create_user("u", email="u@example.com", password="x")
    pref = Preference.objects.create(
        user=user, role_target="developer", budget_min_idr=8000000,
        budget_max_idr=25000000, min_ram_gb=16, min_processor_tier=5,
        min_storage_gb=512,
    )
    rec = generate_recommendation(pref, top_n=5)
    assert isinstance(rec, Recommendation)
    assert len(rec.results) <= 5
    assert 0.0 <= rec.precision_at_k <= 1.0
    sims = [r["similarity"] for r in rec.results]
    assert sims == sorted(sims, reverse=True)


@pytest.mark.django_db
def test_generate_recommendation_without_active_model():
    user = User.objects.create_user("u2", email="u2@example.com", password="x")
    pref = Preference.objects.create(
        user=user, role_target="manajemen", budget_min_idr=5000000,
        budget_max_idr=12000000, min_ram_gb=8, min_processor_tier=3,
        min_storage_gb=256,
    )
    with pytest.raises(NoActiveModel):
        generate_recommendation(pref, top_n=5)
