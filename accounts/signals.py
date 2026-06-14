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
    role = "admin" if instance.email and instance.email in admin_emails else "user"
    Profile.objects.create(user=instance, role=role)
