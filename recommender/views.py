from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.generic import DetailView, ListView, View

from catalog.models import Laptop

from datatable.mixins import DatatableViewMixin
from .exports import build_recommendation_excel, build_recommendation_pdf, recommendations_to_rows
from .forms import PreferenceForm
from .models import Recommendation
from .services import NoActiveModel, generate_recommendation


class RecommendView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, "recommender/recommend.html", {"form": PreferenceForm()})

    def post(self, request):
        form = PreferenceForm(request.POST)
        if not form.is_valid():
            return render(request, "recommender/_form.html", {"form": form})
        pref = form.save(commit=False)
        top_n = int(form.cleaned_data.get("top_n", 5))
        pref.user = request.user
        pref.save()
        try:
            rec = generate_recommendation(pref, top_n=top_n)
        except NoActiveModel as exc:
            return render(request, "recommender/_no_model.html", {"message": str(exc)})
        return render(request, "recommender/_results.html", {"rec": rec})


class HistoryView(LoginRequiredMixin, DatatableViewMixin, ListView):
    template_name = "recommender/history.html"
    context_object_name = "recommendations"
    datatable_columns = [
        {"key": "created_at", "label": "Tanggal", "sortable": True, "searchable": False},
        {"key": "preference__role_target", "label": "Peran", "sortable": False, "searchable": False},
        {"key": "preference__budget_max_idr", "label": "Budget Maks", "sortable": False, "searchable": False, "template": "recommender/_budget_cell.html"},
        {"key": "selected_cluster__interpretation", "label": "Cluster", "sortable": False, "searchable": False, "template": "recommender/_cluster_cell.html"},
        {"key": "precision_at_k", "label": "Precision@K", "sortable": True, "searchable": False, "template": "recommender/_precision_cell.html"},
    ]

    def get_queryset(self):
        return Recommendation.objects.filter(user=self.request.user).select_related(
            "preference", "selected_cluster"
        )


class RecommendationDetailView(LoginRequiredMixin, DetailView):
    model = Recommendation
    template_name = "recommender/result.html"
    context_object_name = "rec"

    def get_queryset(self):
        qs = super().get_queryset().select_related(
            "preference", "selected_cluster", "cluster_model", "user"
        )
        if self.request.user.profile.is_admin:
            return qs
        return qs.filter(user=self.request.user)


class CompareView(LoginRequiredMixin, View):
    def get(self, request):
        raw = request.GET.get("ids", "")
        if not raw:
            return HttpResponseBadRequest("No IDs provided.")

        try:
            ids = [int(i) for i in raw.split(",") if i.strip()][:3]
        except ValueError:
            return HttpResponseBadRequest("Invalid IDs.")

        if not ids:
            return HttpResponseBadRequest("No IDs provided.")

        # Collect all laptop IDs from this user's recommendations
        user_laptop_ids = set()
        for rec in Recommendation.objects.filter(user=request.user):
            for item in rec.results:
                user_laptop_ids.add(item["id"])

        # Security: only allow IDs the user owns
        if not all(i in user_laptop_ids for i in ids):
            return HttpResponseBadRequest("One or more laptops not found in your recommendations.")

        laptops = list(Laptop.objects.filter(id__in=ids).select_related("brand", "processor", "vga"))
        # Preserve requested order
        laptops.sort(key=lambda l: ids.index(l.id))

        return render(request, "recommender/_compare.html", {"laptops": laptops})


class ExportHistoryExcelView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Recommendation.objects.filter(user=request.user)
        rows = recommendations_to_rows(qs, include_user=False)
        content = build_recommendation_excel(rows, include_user_col=False)
        return HttpResponse(
            content,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": 'attachment; filename="riwayat_rekomendasi.xlsx"'},
        )


class ExportHistoryPdfView(LoginRequiredMixin, View):
    def get(self, request):
        qs = Recommendation.objects.filter(user=request.user)
        rows = recommendations_to_rows(qs, include_user=False)
        content = build_recommendation_pdf(rows, include_user_col=False)
        return HttpResponse(
            content,
            content_type="application/pdf",
            headers={"Content-Disposition": 'attachment; filename="riwayat_rekomendasi.pdf"'},
        )


class ExportSingleRecommendationPdfView(LoginRequiredMixin, View):
    def get(self, request, pk):
        qs = Recommendation.objects.filter(pk=pk)
        if not request.user.profile.is_admin:
            qs = qs.filter(user=request.user)
        if not qs.exists():
            return HttpResponseBadRequest("Rekomendasi tidak ditemukan.")
        rows = recommendations_to_rows(qs, include_user=False)
        content = build_recommendation_pdf(rows, include_user_col=False)
        return HttpResponse(
            content,
            content_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="rekomendasi_{pk}.pdf"'},
        )


class ExportSingleRecommendationPdfView(LoginRequiredMixin, View):
    def get(self, request, pk):
        qs = Recommendation.objects.filter(pk=pk)
        if not request.user.profile.is_admin:
            qs = qs.filter(user=request.user)
        if not qs.exists():
            return HttpResponseBadRequest("Rekomendasi tidak ditemukan.")
        rows = recommendations_to_rows(qs, include_user=False)
        content = build_recommendation_pdf(rows, include_user_col=False)
        return HttpResponse(
            content,
            content_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="rekomendasi_{pk}.pdf"'},
        )
