#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.conf.urls.defaults import *
import infsss.views as v


urlpatterns = patterns('',
    
    # mini dashboard for this app
    url(r'^infsss$',
        v.dashboard),
    
    url(r'^infsss/(?P<location>\w+)$',
        v.bylocation),
    
    url(r'^infsss/(?P<type>\w+)$',
        v.people),
    
    url(r'^infsss/(?P<type>\w+)/(?P<id>\d+)$',
        v.bychildid),
    
    url(r'^infsss/(?P<type>\w+)/(?P<id>\d+)$',
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

    url(r'^infsss/(?P<type>\w+)/xls$',
        v.export_xls,
        name="export-xls"),

    #stick in docmanager view
#    url(r'^infsss/(?P<id>\d+)/download$',
#        'django.views.static.serve',{'document_root':'/'}), #File.objects.get(id=1).file.path}),
    
)
