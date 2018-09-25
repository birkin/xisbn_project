# -*- coding: utf-8 -*-

from django.conf.urls import include, url
from django.contrib import admin
from django.views.generic import RedirectView
from xisbn_app import views


admin.autodiscover()


urlpatterns = [

    # url( r'^admin/', admin.site.urls ),  # eg host/project_x/admin/

    url( r'^info/$', views.info, name='info_url' ),

    url( r'^v1/josiah_filtered_alternate_isbns/(?P<isbn_value>.*)/$', views.filtered_alternates, name='josiah_filtered_alternates_url' ),

    url( r'^v1/filtered_alternate_isbns/(?P<isbn_value>.*)/$', views.filtered_alternates, name='filtered_alternates_url' ),

    url( r'^v1/alternate_isbns/(?P<isbn_value>.*)/$', views.alternates, name='alternates_url' ),

    url( r'^$', RedirectView.as_view(pattern_name='info_url') ),

    ]
