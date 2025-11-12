from django.urls import path

from . import views


app_name = "common"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("users", views.IndexView.as_view(), name="index"),
    path("login", views.IndexView.as_view(), name="login"),
    path("signup", views.IndexView.as_view(), name="signup"),
    path("upload", views.IndexView.as_view(), name="upload"),
    path("candidates/<path:id>", views.IndexView.as_view(), name="candidate-detail"),
]
