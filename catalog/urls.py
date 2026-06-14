from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.LaptopListView.as_view(), name="list"),
    path("create/", views.LaptopCreateView.as_view(), name="create"),
    path("<int:pk>/edit/", views.LaptopUpdateView.as_view(), name="update"),
    path("<int:pk>/delete/", views.LaptopDeleteView.as_view(), name="delete"),
]
