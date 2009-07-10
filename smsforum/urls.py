#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
import apps.smsforum.views as views

urlpatterns = patterns('',
    url(r'^$',                               views.index),
    url(r'^villages$',                       views.index),
    url(r'^village/(?P<pk>\d+)$',            views.members),
    url(r'^village/add$',                    views.add_village),
    url(r'^village/edit/(?P<pk>\d+)$',       views.edit_village),
    url(r'^village/(?P<village_id>\d+)/member/add$', views.add_member),
    url(r'^village/(?P<pk>\d+)/history$', views.village_history),
    url(r'^member/(?P<pk>\d+)$',             views.member),
    url(r'^member/add$',                     views.add_member),
    url(r'^member/edit/(?P<pk>\d+)$',        views.edit_member),
    url(r'^i18n/',                           include('django.conf.urls.i18n')),
    #url(r'^community/add$',                 views.add_community),
)

