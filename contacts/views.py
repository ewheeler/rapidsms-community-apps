#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from rapidsms.webui.utils import render_to_response, paginated
from apps.contacts.models import Contact
from apps.reporting.util import export

def index(req, template="contacts/index.html"):
    context = {}
    contacts = Contact.objects.all()
    context['contacts'] = paginated(req, contacts)
    return render_to_response(req, template, context)

def csv(req, format='csv'):
    if req.user.is_authenticated():
        return export(Contact.objects.all(), \
            ['id','node_ptr','first_seen','given_name','family_name',\
             'common_name','unique_id','location','gender','age_months','_locale'])
    return export(Contact.objects.all(), \
        ['id','node_ptr','first_seen','location','gender','age_months','_locale'])
