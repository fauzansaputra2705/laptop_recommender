from django.urls import path

from . import views

app_name = "clustering"

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("train/", views.TrainView.as_view(), name="train"),
    path("evaluate/", views.EvaluateView.as_view(), name="evaluate"),
]
