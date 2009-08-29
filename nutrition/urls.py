#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
import views as v


urlpatterns = patterns('',
    
    # mini dashboard for this app
    url(r'^nutrition$',
        v.dashboard,
        name="nutrition"),

)

#edit data in the admin interface 
#import via csv - someplace too
