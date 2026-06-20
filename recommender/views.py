from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import render
from django.views.generic import ListView, View

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
        pref.user = request.user
        pref.save()
        try:
            rec = generate_recommendation(pref, top_n=5)
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
