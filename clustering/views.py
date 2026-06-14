from django.shortcuts import render
from django.views.generic import TemplateView

from accounts.mixins import AdminRequiredMixin
from clustering.models import ClusterModel
from clustering.services import run_training


class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = "clustering/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model = ClusterModel.objects.filter(is_active=True).first()
        ctx["model"] = model
        ctx["clusters"] = model.clusters.all() if model else []
        return ctx


class TrainView(AdminRequiredMixin, TemplateView):
    """POST-only: runs training, returns an HTMX partial."""

    def post(self, request, *args, **kwargs):
        try:
            model = run_training()
        except ValueError as exc:
            return render(
                request,
                "clustering/_train_error.html",
                {"message": str(exc)},
            )
        return render(
            request,
            "clustering/_train_result.html",
            {"model": model, "clusters": model.clusters.all()},
        )
