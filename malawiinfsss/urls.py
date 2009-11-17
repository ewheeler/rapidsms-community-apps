#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
import views as v


urlpatterns = patterns('',
    
    # mini dashboard for this app
    url(r'^malawi$',
        v.dashboard,
        name="malawi"),

    url(r'^malawi/data$',
        v.view_all_data,
        name="all_data"),

    url(r'^malawi/gmc$',
        v.view_all_gmc,
        name="all_gmc"),

    url(r'^malawi/patients$',
        v.view_all_patients,
        name="all_patients"),

    url(r'^malawi/(?P<date1>\d+)/(?P<date2>\d+)$',
        v.view_by_date_range,
        name="view_by_date_range")
)

#edit data in the admin interface 
#import via csv - someplace too
