from django.conf.urls import include, url
from django.contrib.gis import admin
from rest_framework.documentation import include_docs_urls
import settings

from apps.api2.urls import urlpatterns as v2urls
from apps.api.urls import urlpatterns as v1urls
from apps.widget.urls import urlpatterns as widgeturls
# Uncomment the next two lines to enable the admin:
admin.autodiscover()

urlpatterns = [
    # APPS de CualBondi
    url(r'^v2/', include(v2urls)),
    url(r'^api/v2/', include(v2urls)),
    url(r'^api/v1/', include(v1urls)),
    url(r'^api/', include(v1urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^widget/', include(widgeturls)),
    url(r'^docs/', include_docs_urls(title='Cualbondi API')),
    url(r'^', include(v2urls)),
]
