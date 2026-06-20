import pytest

from catalog.models import Laptop
from clustering.models import Cluster, ClusterModel
from clustering.services import run_training


@pytest.mark.django_db
def test_run_training_rejects_insufficient_data(make_laptops):
    make_laptops(5)
    with pytest.raises(ValueError):
        run_training()


@pytest.mark.django_db
def test_run_training_creates_active_model_and_labels(make_laptops):
    make_laptops(60)
    model = run_training()
    assert model.is_active
    assert ClusterModel.objects.filter(is_active=True).count() == 1
    assert Cluster.objects.filter(cluster_model=model).count() == model.k_optimal
    assert Laptop.objects.filter(cluster_label__isnull=True).count() == 0
    assert model.wcss_list
    assert model.silhouette_list
