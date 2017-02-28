from django.conf.urls import url
from django.contrib import admin

from devices import views


urlpatterns = [
    url(r'^smartadmin/', admin.site.urls),
    url(r'^poweron/(?P<device>[0-9]{1,5})/$', views.poweron),
    url(r'^poweroff/(?P<device>[0-9]{1,5})/$', views.poweroff),
    url(r'^poweron/all/$', views.poweron_all),
    url(r'^poweroff/all/$', views.poweroff_all),
    url(r'^status/(?P<device>[0-9]{1,5})/$', views.status),
]
