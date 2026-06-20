from django.urls import path

from . import views

app_name = "recommender"

urlpatterns = [
    path("", views.RecommendView.as_view(), name="recommend"),
    path("history/", views.HistoryView.as_view(), name="history"),
    path("export/excel/", views.ExportHistoryExcelView.as_view(), name="export_excel"),
    path("export/pdf/", views.ExportHistoryPdfView.as_view(), name="export_pdf"),
]
