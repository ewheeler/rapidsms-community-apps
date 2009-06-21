#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
import apps.smsforum.views as views

urlpatterns = patterns('',
    url(r'^villages$',                      views.index),
    url(r'^village/(?P<pk>\d+)$',          views.members),
    url(r'^village/edit/(?P<pk>\d+)$',      views.edit_village),
    url(r'^member/(?P<pk>\d+)$',   views.member),
    url(r'^member/edit/(?P<pk>\d+)$',      views.edit_member),
    #url(r'^village/add$',   views.add_village),
    url(r'^community/add$',   views.add_community),
)

