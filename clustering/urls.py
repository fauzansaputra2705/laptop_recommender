from django.urls import path

from . import views
from .calc_views import ManualCalcView

app_name = "clustering"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("train/", views.TrainView.as_view(), name="train"),
    path("evaluate/", views.EvaluateView.as_view(), name="evaluate"),
    path("manual-calc/", ManualCalcView.as_view(), name="manual_calc"),
]
