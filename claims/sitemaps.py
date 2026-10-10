from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    protocol = "https"
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        # /result/ is per-session, so it stays out of the sitemap
        return ["landing", "how_it_works", "claim_submit"]

    def location(self, item):
        return reverse(item)