from django.urls import include, path
from . import views

urlpatterns = [
    path("", views.home_pg, name="home page")
]