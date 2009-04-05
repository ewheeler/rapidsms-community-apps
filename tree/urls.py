#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import os
from django.conf.urls.defaults import *
import apps.tree.views as views

urlpatterns = patterns('',
    url(r'^tree$', views.index),
    
    # serve the static files for this TREE app
    # TODO: this should be automatic, via WEBUI
    (r'^static/tree/(?P<path>.*)$', "django.views.static.serve",
        {"document_root": os.path.dirname(__file__) + "/static"})
)
