from django.urls import path

from .views import WorkspaceDetailView, WorkspaceListCreateView

urlpatterns = [
    path("", WorkspaceListCreateView.as_view()),
    path("<int:pk>/", WorkspaceDetailView.as_view()),
]