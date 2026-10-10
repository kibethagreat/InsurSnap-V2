from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from claims.sitemaps import StaticViewSitemap

from . import views

sitemaps = {"static": StaticViewSitemap}

urlpatterns = [
    path("", views.landing, name="landing"),
    path("how-it-works/", views.how_it_works, name="how_it_works"),
    path("file/", views.claim_submit, name="claim_submit"),
    path("result/", views.claim_result, name="claim_result"),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="django.contrib.sitemaps.views.sitemap"),
    path("robots.txt", TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
    
]
