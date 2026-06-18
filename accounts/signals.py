from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Profile


@receiver(post_save, sender=User)
def ensure_profile(sender, instance, created, **kwargs):
    if not created:
        return
    admin_emails = getattr(settings, "ADMIN_EMAILS", [])
    is_admin = (instance.is_staff or instance.is_superuser or
                (instance.email and instance.email in admin_emails))
    role = "admin" if is_admin else "user"
    Profile.objects.create(user=instance, role=role)
