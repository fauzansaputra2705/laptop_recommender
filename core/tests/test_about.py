import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_about_accessible_anonymous(client):
    resp = client.get(reverse("core:about"))
    assert resp.status_code == 200
    assert b"K-Means" in resp.content


@pytest.mark.django_db
def test_about_contains_key_sections(client):
    resp = client.get(reverse("core:about"))
    content = resp.content
    assert b"Cosine Similarity" in content
    assert b"Silhouette" in content
    assert b"PT Informatika Media Pratama" in content
