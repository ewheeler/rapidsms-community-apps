#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from rapidsms.webui.utils import render_to_response, paginated
from apps.contacts.models import Contact
from apps.contacts.forms import *
from utilities.export import export

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

@login_required
def add_contact(req, template="contacts/add.html"):
    context = {}
    if req.method == 'POST':
        form = ContactForm(req.POST)
        if form.is_valid():
            c = form.save()
            context['status'] = _("Contact '%(member_name)s' successfully created" % {'member_name':c.signature} )
        else:
            context['error'] = form.errors
    context['form'] = ContactForm()
    context['title'] = _("Add Member")
    return render_to_response(req, template, context)    

@login_required
def edit_contact(req, pk, template="contacts/edit.html"):
    context = {}
    contact = get_object_or_404(Contact, id=pk)
    if req.method == "POST":
        form = create_contact_if_valid(req.POST, contact)
        context['error'] = form.errors
        context['status'] = _("Contact '%(contact_name)s' successfully updated" % \
                            {'contact_name':contact.signature} )
    else:
        form = get_contact_form(instance=contact)
    context['form'] = form
    context['title'] = _("Edit Member")
    return render_to_response(req, template, context)
