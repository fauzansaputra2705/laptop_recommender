import pytest
from django.core.management import call_command

from catalog.models import Laptop
from clustering.models import Cluster, ClusterModel
from clustering.services import run_training


def _make_laptops(n):
    call_command("generate_dummy_laptops", "--count", str(n), "--seed", "1")


@pytest.mark.django_db
def test_run_training_rejects_insufficient_data():
    _make_laptops(5)
    with pytest.raises(ValueError):
        run_training()


@pytest.mark.django_db
def test_run_training_creates_active_model_and_labels():
    _make_laptops(60)
    model = run_training()
    assert model.is_active
    assert ClusterModel.objects.filter(is_active=True).count() == 1
    assert Cluster.objects.filter(cluster_model=model).count() == model.k_optimal
    assert Laptop.objects.filter(cluster_label__isnull=True).count() == 0
    assert model.elbow_plot.name
    assert model.silhouette_plot.name
