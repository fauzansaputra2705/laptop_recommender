from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class AdminRequiredMixin(LoginRequiredMixin):
    """Authenticated user with admin role; otherwise 403."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        if not request.user.profile.is_admin:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)


class UserRequiredMixin(LoginRequiredMixin):
    """Any authenticated user (admin or user) may access."""
