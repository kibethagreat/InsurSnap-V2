from django.urls import path

from . import views

urlpatterns = [
    path("", views.landing, name="landing"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("file/", views.claim_submit, name="claim_submit"),
    path("result/", views.claim_result, name="claim_result"),
]
