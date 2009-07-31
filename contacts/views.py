#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.utils.translation import ugettext as _
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from rapidsms.webui.utils import render_to_response, paginated
from apps.contacts.models import Contact
from apps.contacts.forms import *
from utilities.export import export

def index(request, template="contacts/index.html"):
    context = {}
    contacts = Contact.objects.all()
    context['contacts'] = paginated(request, contacts)
    return render_to_response(request, template, context)

def csv(request, format='csv'):
    if request.user.is_authenticated():
        return export(Contact.objects.all(), \
            ['id','node_ptr','first_seen','given_name','family_name',\
             'common_name','unique_id','location','gender','age_months','_locale'])
    return export(Contact.objects.all(), \
        ['id','node_ptr','first_seen','location','gender','age_months','_locale'])

@login_required
def add_contact(request, template="contacts/add.html"):
    context = {}
    if request.method == 'POST':
        form = GSMContactForm(request.POST)
        if form.is_valid():
            c = form.save()
            context['status'] = _("Contact '%(member_name)s' successfully created" % {'member_name':c.signature} )
        else:
            context['error'] = form.errors
    context['form'] = GSMContactForm()
    context['title'] = _("Add Member")
    return render_to_response(request, template, context)    

@login_required
def edit_contact(request, pk, template="contacts/edit.html"):
    context = {}
    contact = get_object_or_404(Contact, id=pk)
    if request.method == "POST":
        form = GSMContactForm(request.POST, contact)
        if form.is_valid():
            form.save()
            context['status'] = _("Contact '%(contact_name)s' successfully updated" % \
                                {'contact_name':contact.signature} )
        else:
            context['error'] = form.errors
    else:
        form = GSMContactForm(instance=contact)
    context['form'] = form
    context['title'] = _("Edit Member") + " " + contact.signature
    context['contact'] = contact
    return render_to_response(request, template, context)

@login_required()
def delete_contact(request, pk, template='contacts/confirm_delete.html'):
    context = {}
    contact = get_object_or_404(Contact, id=pk)    
    if request.method == "POST":
        if request.POST["confirm_delete"]: # The user has already confirmed the deletion.
            # TODO - currently this also deletes any associated logs from the db
            contact.delete()
            return HttpResponseRedirect("../../contacts")
    context['contact'] = contact
    return render_to_response(request, template, context)

