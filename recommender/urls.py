from django.urls import path

from . import views

app_name = "recommender"

urlpatterns = [
    path("", views.RecommendView.as_view(), name="recommend"),
    path("history/", views.HistoryView.as_view(), name="history"),
]
