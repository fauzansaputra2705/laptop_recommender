from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.LandingView.as_view(), name="landing"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("admin-login/", views.AdminLoginView.as_view(), name="admin_login"),
    path("dashboard/users/", views.ProfileListView.as_view(), name="manage_users"),
    path("dashboard/users/<int:pk>/toggle-role/", views.ToggleRoleView.as_view(), name="toggle_role"),
    path("dashboard/models/", views.ClusterModelListView.as_view(), name="manage_models"),
    path("dashboard/models/<int:pk>/activate/", views.ActivateModelView.as_view(), name="activate_model"),
    path("dashboard/recommendations/", views.RecommendationListView.as_view(), name="manage_recommendations"),
    path("dashboard/usecase/", views.UsecaseView.as_view(), name="usecase"),
]
