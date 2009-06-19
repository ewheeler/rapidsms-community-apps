#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
import apps.smsforum.views as views


urlpatterns = patterns('',
    url(r'^villages$',                      views.index),
    url(r'^villages/(?P<pk>\d+)$',          views.edit_village),
    url(r'^villages/member/(?P<pk>\d+)$',   views.edit_member),
)

