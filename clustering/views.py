from django.db.models import Sum
from django.shortcuts import render
from django.views.generic import TemplateView

from accounts.mixins import AdminRequiredMixin
from clustering.models import ClusterModel
from clustering.plots import cluster_distribution_png, comparison_bar_png
from clustering.services import run_training


class DashboardView(AdminRequiredMixin, TemplateView):
    template_name = "clustering/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        model = ClusterModel.objects.filter(is_active=True).first()
        ctx["model"] = model
        clusters = list(model.clusters.all()) if model else []
        ctx["clusters"] = clusters
        if model and clusters:
            ctx["dist_chart_b64"] = cluster_distribution_png(
                [c.label for c in clusters],
                [c.member_count for c in clusters],
                [c.interpretation for c in clusters],
            )
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


class EvaluateView(AdminRequiredMixin, TemplateView):
    template_name = "clustering/evaluate.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        models = list(ClusterModel.objects.prefetch_related("clusters").order_by("-created_at"))
        # annotate each model with total_laptops (sum of member_count across clusters)
        for m in models:
            m.total_laptops = sum(c.member_count for c in m.clusters.all())
        labels = [f"#{m.pk}" for m in models]
        scores = [m.silhouette_score for m in models]
        active_idx = next((i for i, m in enumerate(models) if m.is_active), None)
        ctx["models"] = models
        ctx["chart_b64"] = comparison_bar_png(labels, scores, active_idx) if models else None
        return ctx
