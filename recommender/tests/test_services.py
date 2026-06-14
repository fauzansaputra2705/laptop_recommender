import pytest
from django.contrib.auth.models import User
from django.core.management import call_command

from clustering.services import run_training
from recommender.models import Preference, Recommendation
from recommender.services import NoActiveModel, generate_recommendation


@pytest.mark.django_db
def test_generate_recommendation_end_to_end():
    call_command("generate_dummy_laptops", "--count", "80", "--seed", "3")
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
