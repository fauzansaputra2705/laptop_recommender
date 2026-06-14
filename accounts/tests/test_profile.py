import pytest
from django.contrib.auth.models import User

from accounts.models import Profile


@pytest.mark.django_db
def test_profile_created_on_user_create():
    user = User.objects.create_user("u1", email="u1@example.com", password="x")
    assert Profile.objects.filter(user=user).exists()
    assert user.profile.role == "user"


@pytest.mark.django_db
def test_admin_email_gets_admin_role(settings):
    settings.ADMIN_EMAILS = ["boss@example.com"]
    user = User.objects.create_user("boss", email="boss@example.com", password="x")
    assert user.profile.role == "admin"
