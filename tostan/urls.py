#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
import tostan.views as views

urlpatterns = patterns('',
    url(r'^smscommands/?$',  views.smscommands),
)
