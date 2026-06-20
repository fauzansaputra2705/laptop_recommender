from django.urls import path

from . import views

app_name = "recommender"

urlpatterns = [
    path("", views.RecommendView.as_view(), name="recommend"),
    path("history/", views.HistoryView.as_view(), name="history"),
    path("result/<int:pk>/", views.RecommendationDetailView.as_view(), name="result"),
    path("compare/", views.CompareView.as_view(), name="compare"),
    path("export/excel/", views.ExportHistoryExcelView.as_view(), name="export_excel"),
    path("export/pdf/", views.ExportHistoryPdfView.as_view(), name="export_pdf"),
]
