#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError
from django.template import RequestContext
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from django.contrib.auth.decorators import permission_required
from django.shortcuts import get_object_or_404
from django.db import transaction

from rapidsms.webui.utils import *
from apps.smsforum.models import *
from apps.smsforum.utils import *
from apps.smsforum.forms import *
from apps.smsforum.app import CMD_MESSAGE_MATCHER
from apps.logger.models import *
from apps.contacts.models import *
from apps.contacts.forms import *

from datetime import datetime, timedelta

def index(req, template="smsforum/index.html"):
    context = {}
    if req.method == 'POST':    
        # now iterate through all the messages you learned about
        for i in req.POST.getlist('message'):
            id = int(i)
            m = IncomingMessage.objects.select_related().get(id=id)
            # GATHER EXISTING TAGS
            tags = MessageTag.objects.select_related().filter(message=m)
            flag = None
            code = None
            for tag in tags:
                if tag.code.set.name == "FLAGGED_CODE":
                    flag = tag 
                elif tag.code.set.name == "TOSTAN_CODE":
                    code = tag
            note = None
            notes = MessageAnnotation.objects.filter(message=m)
            if len(notes) > 0: note = notes[0]
            
            # CHECK FOR SUBMITTED VALUES
            if 'flagged_'+ str(id) in req.POST: flag_bool = True
            else: flag_bool = False
            note_txt = req.POST['text_'+str(id)]
            code_txt = req.POST['code_'+str(id)]
            
            # MAP SUBMITTED VALUES TO NEW DB STATE
            if flag is None:
                if flag_bool == True:
                    flag = MessageTag(message=m)
                    SetFlag(flag)
                    flag.save()
            else:
                if flag_bool == False: flag.delete()
                else:
                    SetFlag(flag)
                    flag.save()
                    
            if code is None:
                if len(code_txt) > 0:
                    code = MessageTag(message=m)
                    code = SetCode(code,code_txt)
                    code.save()
            else:
                if len(code_txt) == 0: code.delete()
                else:
                    SetCode(code,code_txt)
                    code.save() 
                                   
            if note is None:
                if len(note_txt) > 0:
                    note = MessageAnnotation(message=m)
                    note.text = note_txt
                    note.save()
            else:
                if len(note_txt) == 0: note.delete()
                else:
                    note.text = note_txt
                    note.save()                
    villages = Village.objects.all()
    for village in villages:
        # once this site bears more load, we can replace flatten() with village.subnodes
        # and stop reporting num_messages
        village.member_count = len( village.flatten() )
        last_week = ( datetime.now()-timedelta(weeks=1) )
        village.message_count = IncomingMessage.objects.filter(domain=village,received__gte=last_week).count()
        # TODO - fix this number
        village.messages_sent_count = village.message_count * village.member_count
    context['villages'] = paginated(req, villages)
    messages = IncomingMessage.objects.select_related().order_by('-received')
    context.update( format_messages_in_context(req, context, messages) )
    context.upate( totals(context) )
    return render_to_response(req, template, context)

def format_messages_in_context(req, context, messages):
    cmd_messages = []
    blast_messages = []
    for msg in messages:
        for tag in msg.messagetag_set.all():
            if IsFlag(tag): msg.flagged = True
            elif tag.code.set.name == "TOSTAN_CODE": msg.code = tag.code
        notes = msg.messageannotation_set.filter(message=msg)
        if len(notes) > 0: msg.note = notes[0].text
        # are we a command?
        m=CMD_MESSAGE_MATCHER.match(msg.text)
        if m is None: blast_messages.append(msg)
        else: cmd_messages.append(msg)
    if len(cmd_messages)>0:
        context['cmd_messages'] = paginated(req, cmd_messages, per_page=10, prefix="cmd")
    if len(blast_messages)>0:
        context['blast_messages'] = paginated(req, blast_messages, per_page=10, prefix="blast")
    context['codes'] = Code.objects.filter(set=CodeSet.objects.get(name="TOSTAN_CODE"))
    return context


# TODO: move this somewhere Tostan-Specifig
# would declare this as a class but we don't need the extra database table
def SetFlag(flag):
    code = Code.objects.get(slug="True")
    flag.code = code

def IsFlag(tag):
    if tag.code.set.name == "FLAGGED_CODE": return True
    else: return False

# would declare this as a class but we don't need the extra database table
def SetCode(tag, str):
    code = Code.objects.get(slug=str)
    tag.code = code
    return tag

def members(req, pk, template="smsforum/members.html"):
    context = {}
    village = Village.objects.get(id=pk)
    members = village.flatten(klass=Contact)
    for member in members:
        connections = ChannelConnection.objects.filter(contact=member)
        if len(connections) > 0:
            # we can always click on the user to see a list of all their connections
            member.phone_number = connections[0].user_identifier
            last_week = ( datetime.now()-timedelta(weeks=1) )
            member.message_count = IncomingMessage.objects.filter(identity=member.phone_number,received__gte=last_week).count()
    context['village'] = village
    context['members'] = paginated(req, members)
    messages = IncomingMessage.objects.filter(domain=village).order_by('-received')
    format_messages_in_context(req, context, messages)
    return render_to_response(req, template, context)

def member(req, pk, template="smsforum/member.html"):
    context = {}
    contact = Contact.objects.get(id=pk)
    if req.method == "POST":
        if req.POST["message_body"]:
            pass
            """
            be = self.router.get_backend(pconn.backend.slug)
            return be.message(pconn.identity, form["text"]).send()
            
            xformmanager = XFormManager()
            xformmanager.remove_schema(form_id)
            logging.debug("Schema %s deleted ", form_id)
            #self.message_user(request, _('The %(name)s "%(obj)s" was deleted successfully.') % {'name': force_unicode(opts.verbose_name), 'obj': force_unicode(obj_display)})                    
            return HttpResponseRedirect("../register")
            """
    try:
        connections = ChannelConnection.objects.get(contact=contact)
        contact.phone_number = connections.user_identifier
        last_week = ( datetime.now()-timedelta(weeks=1) )
        messages = IncomingMessage.objects.filter(identity=contact.phone_number,received__gte=last_week).order_by('-received')
        contact.message_count = len(messages)
        format_messages_in_context(req, context, messages)
    except ChannelConnection.DoesNotExist:
        #this is a contact without a phone number
        pass
    context['member'] = contact
    return render_to_response(req, template, context)

def edit_village(req, pk, template="smsforum/edit.html"):
    context = {}
    form = get_object_or_404(Village, id=pk)
    if req.method == "POST":
        f = VillageForm(req.POST, instance=form)
        f.save()
    context['form'] = VillageForm(instance=form)
    context['title'] = _("Edit Village")
    return render_to_response(req, template, context)
    
def edit_member(req, pk, template="smsforum/edit.html"):
    context = {}
    contact = get_object_or_404(Contact, id=pk)
    if req.method == "POST":
        form = create_contact_from_post(req.POST, contact)
    else:
        form = get_contact_form(instance=contact)
    context['form'] = form
    context['title'] = _("Edit Member")
    return render_to_response(req, template, context)

def add_village(req, template="smsforum/add.html"):
    context = {}
    if req.method == 'POST':
        form = VillageForm(req.POST)
        if form.is_valid():
            v,created =Village.objects.get_or_create( name=form.cleaned_data['name'] )
            if created:
                context['status'] = _("Village '%(village_name)s' successfully created" % {'village_name':v.name} )
            else:
                context['status'] = _("Village already exists!")
        else:
                context['status'] = _("Form invalid")
    context['form'] = VillageForm()
    context['title'] = _("Add Village")
    return render_to_response(req, template, context)    

def add_member(req, village_id=0, template="smsforum/add.html"):
    context = {}
    if req.method == 'POST':
        form = ContactForm(req.POST)
        if form.is_valid():
            c = form.save()
            c.add_to_parent( Village.objects.get(id=village_id) )
            context['status'] = _("Member '%(member_name)s' successfully created" % {'member_name':c.signature} )
        else:
            context['error'] = form.errors
    context['form'] = ContactForm()
    context['title'] = _("Add Member")
    return render_to_response(req, template, context)    


def totals(context):
    context['village_count'] = Village.objects.all().count()
    context['member_count'] = Contact.objects.all().count()
    context['incoming_message_count'] = IncomingMessage.objects.all().count()
    return context
