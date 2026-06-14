import pytest
from django.contrib.auth.models import User

from clustering.models import Cluster, ClusterModel
from recommender.models import Preference, Recommendation


@pytest.mark.django_db
def test_recommendation_links_preference_and_cluster():
    user = User.objects.create_user("u", email="u@example.com", password="x")
    pref = Preference.objects.create(
        user=user, role_target="developer", budget_min_idr=8000000,
        budget_max_idr=20000000, min_ram_gb=16, min_processor_tier=5,
        min_storage_gb=512,
    )
    cm = ClusterModel.objects.create(
        k_optimal=3, silhouette_score=0.6, centroids=[], wcss_list=[],
        silhouette_list=[], scaler_params={}, feature_order=[], is_active=True,
    )
    cl = Cluster.objects.create(
        cluster_model=cm, label=1, interpretation="Mid-Range",
        centroid=[], member_count=5, summary={},
    )
    rec = Recommendation.objects.create(
        user=user, preference=pref, cluster_model=cm, selected_cluster=cl,
        results=[{"id": 1, "similarity": 0.9}], precision_at_k=0.8, k_value=5,
    )
    assert rec.preference == pref
    assert rec.selected_cluster.interpretation == "Mid-Range"
    assert user.recommendations.count() == 1
