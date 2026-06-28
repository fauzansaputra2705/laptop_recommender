from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, TemplateView

from accounts.mixins import AdminRequiredMixin
from clustering.models import ClusterModel
from datatable.mixins import DatatableViewMixin
from recommender.exports import build_recommendation_excel, build_recommendation_pdf, recommendations_to_rows
from recommender.models import Recommendation


class LandingView(TemplateView):
    template_name = "core/landing.html"


class AboutView(TemplateView):
    template_name = "core/about.html"


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "core/dashboard.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        is_admin = self.request.user.profile.is_admin
        ctx["is_admin"] = is_admin

        if is_admin:
            import datetime

            from catalog.models import Laptop
            from clustering.models import Cluster
            from django.db.models import Avg, Count
            from django.db.models.functions import TruncDate
            from django.utils import timezone

            from core.plots import cluster_usage_png, precision_trend_png, role_distribution_png

            ctx["total_laptops"] = Laptop.objects.count()
            ctx["total_clusters"] = Cluster.objects.filter(cluster_model__is_active=True).count()
            ctx["total_users"] = User.objects.count()
            ctx["total_recommendations"] = Recommendation.objects.count()
            ctx["avg_precision"] = Recommendation.objects.aggregate(
                avg=Avg("precision_at_k")
            )["avg"] or 0
            ctx["active_clusters"] = Cluster.objects.filter(
                cluster_model__is_active=True
            ).select_related("cluster_model").order_by("label")
            ctx["recent_recommendations"] = Recommendation.objects.select_related(
                "user", "preference", "selected_cluster"
            ).order_by("-created_at")[:5]

            if Recommendation.objects.exists():
                role_qs = (
                    Recommendation.objects.values("preference__role_target")
                    .annotate(count=Count("id"))
                    .order_by()
                )
                ctx["chart_role"] = role_distribution_png(
                    [r["preference__role_target"] or "(unknown)" for r in role_qs],
                    [r["count"] for r in role_qs],
                )

                since = timezone.now().date() - datetime.timedelta(days=30)
                trend_qs = (
                    Recommendation.objects.filter(created_at__date__gte=since)
                    .annotate(day=TruncDate("created_at"))
                    .values("day")
                    .annotate(avg_p=Avg("precision_at_k"))
                    .order_by("day")
                )
                ctx["chart_precision"] = precision_trend_png(
                    [r["day"] for r in trend_qs],
                    [float(r["avg_p"]) for r in trend_qs],
                ) if trend_qs.exists() else None

                cluster_qs = (
                    Recommendation.objects.values("selected_cluster__interpretation")
                    .annotate(count=Count("id"))
                    .order_by()
                )
                ctx["chart_cluster"] = cluster_usage_png(
                    [r["selected_cluster__interpretation"] or "(unknown)" for r in cluster_qs],
                    [r["count"] for r in cluster_qs],
                )
            else:
                ctx["chart_role"] = None
                ctx["chart_precision"] = None
                ctx["chart_cluster"] = None
        else:
            user_recs = self.request.user.recommendations.select_related(
                "preference", "selected_cluster"
            )
            ctx["user_recommendation_count"] = user_recs.count()
            last = user_recs.first()
            ctx["user_last_precision"] = last.precision_at_k if last else None
            ctx["user_last_date"] = last.created_at if last else None
            ctx["user_recent_recommendations"] = user_recs[:5]

        return ctx


class AdminLoginView(View):
    def post(self, request):
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return HttpResponseRedirect(reverse("core:dashboard"))
        return HttpResponseRedirect(reverse("account_login") + "?error=1")


# --- Admin Management Views ---


class ProfileListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = User
    template_name = "core/manage_users.html"
    context_object_name = "users"
    datatable_columns = [
        {"key": "username", "label": "Username", "sortable": True, "searchable": True},
        {"key": "email", "label": "Email", "sortable": False, "searchable": True},
        {"key": "role", "label": "Role", "sortable": False, "searchable": False, "template": "core/_user_role_cell.html"},
        {"key": "is_staff", "label": "Staff", "sortable": True, "searchable": False, "template": "core/_user_staff_cell.html"},
        {"key": "date_joined", "label": "Bergabung", "sortable": True, "searchable": False},
        {"key": "actions", "label": "Aksi", "sortable": False, "searchable": False, "template": "core/_user_actions.html"},
    ]

    def get_queryset(self):
        return User.objects.select_related("profile").order_by("-date_joined")


class ToggleRoleView(AdminRequiredMixin, View):
    def post(self, request, pk):
        try:
            user = User.objects.select_related("profile").get(pk=pk)
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse("core:manage_users"))
        profile = user.profile
        profile.role = "user" if profile.is_admin else "admin"
        profile.save()
        return HttpResponseRedirect(reverse("core:manage_users"))


class ClusterModelListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = ClusterModel
    template_name = "core/manage_models.html"
    context_object_name = "models"
    datatable_columns = [
        {"key": "pk", "label": "ID", "sortable": True, "searchable": False},
        {"key": "k_optimal", "label": "K Optimal", "sortable": True, "searchable": False, "mono": True},
        {"key": "silhouette_score", "label": "Silhouette", "sortable": True, "searchable": False, "mono": True},
        {"key": "is_active", "label": "Status", "sortable": False, "searchable": False, "template": "core/_model_status_cell.html"},
        {"key": "created_at", "label": "Dibuat", "sortable": True, "searchable": False},
        {"key": "actions", "label": "Aksi", "sortable": False, "searchable": False, "template": "core/_model_actions.html"},
    ]


class ActivateModelView(AdminRequiredMixin, View):
    def post(self, request, pk):
        try:
            model = ClusterModel.objects.get(pk=pk)
        except ClusterModel.DoesNotExist:
            return HttpResponseRedirect(reverse("core:manage_models"))
        model.is_active = True
        model.save()
        return HttpResponseRedirect(reverse("core:manage_models"))


class RecommendationListView(AdminRequiredMixin, DatatableViewMixin, ListView):
    model = Recommendation
    template_name = "core/manage_recommendations.html"
    context_object_name = "recommendations"
    datatable_columns = [
        {"key": "pk", "label": "ID", "sortable": True, "searchable": False},
        {"key": "user__username", "label": "User", "sortable": True, "searchable": True},
        {"key": "preference__role_target", "label": "Role Target", "sortable": False, "searchable": True, "template": "core/_role_target_cell.html"},
        {"key": "precision_at_k", "label": "Precision@K", "sortable": True, "searchable": False, "mono": True},
        {"key": "created_at", "label": "Tanggal", "sortable": True, "searchable": False},
    ]

    def get_queryset(self):
        return Recommendation.objects.select_related(
            "user", "preference", "selected_cluster", "cluster_model"
        ).order_by("-created_at")


class UsecaseView(AdminRequiredMixin, TemplateView):
    template_name = "core/usecase.html"
