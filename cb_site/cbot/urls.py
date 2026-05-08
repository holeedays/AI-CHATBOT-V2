from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_pg, name="home page"),
    path("compression-status/", views.compression_status, name="compression status"),
    path("font-preference/", views.font_preference, name="font preference"),
]
