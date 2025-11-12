from django.urls import path
from . import api_views

urlpatterns = [
    path('user/', api_views.current_user, name='current-user'),
]

