import pytest

from clustering.models import Cluster, ClusterModel


@pytest.mark.django_db
def test_only_one_active_model():
    m1 = ClusterModel.objects.create(
        k_optimal=3, silhouette_score=0.6, centroids=[], wcss_list=[],
        silhouette_list=[], scaler_params={}, feature_order=[], is_active=True,
    )
    m2 = ClusterModel.objects.create(
        k_optimal=4, silhouette_score=0.7, centroids=[], wcss_list=[],
        silhouette_list=[], scaler_params={}, feature_order=[], is_active=True,
    )
    m1.refresh_from_db()
    assert ClusterModel.objects.filter(is_active=True).count() == 1
    assert m2.is_active is True
    assert m1.is_active is False


@pytest.mark.django_db
def test_cluster_belongs_to_model():
    m = ClusterModel.objects.create(
        k_optimal=2, silhouette_score=0.5, centroids=[], wcss_list=[],
        silhouette_list=[], scaler_params={}, feature_order=[], is_active=True,
    )
    c = Cluster.objects.create(
        cluster_model=m, label=0, interpretation="Entry-Level",
        centroid=[], member_count=10, summary={},
    )
    assert c.cluster_model == m
    assert m.clusters.count() == 1
