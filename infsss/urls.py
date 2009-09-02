#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
from apps.docmanager.models import *

import views as v


urlpatterns = patterns('',
    
    # mini dashboard for this app
    url(r'^infsss$',
        v.dashboard),
    
    url(r'^infsss/(?P<location>Country|Region|District|GMC)$',
        v.bylocation),
    
    url(r'^infsss/(?P<type>Child|HSA)$',
        v.people),
    
    url(r'^infsss/(?P<type>Child)/(?P<id>\d+)$',
        v.bychildid),
    
    url(r'^infsss/(?P<type>HSA)/(?P<id>\d+)$',
        v.byhsaid),

    url(r'^infsss/region/(?P<id>\d+)$',
        v.bylocationid),
    

    url(r'^infsss/(?P<date1>\d+)-(?P<date2>\d+)$',
        v.data_date_filter),
    
    url(r'^infsss/date$',
        v.datefilter),
   
   url(r'^infsss/(?P<id>\d+)/download$',
        v.download_file,
        name='download-file'),

    url(r'^infsss/(?P<type>Nutrition|Wasting|Stunting|Children|HSAs|Location)/xls$',
        v.export_xls,
        name="export-xls"),

    #stick in docmanager view
#    url(r'^infsss/(?P<id>\d+)/download$',
#        'django.views.static.serve',{'document_root':'/'}), #File.objects.get(id=1).file.path}),
    
)
