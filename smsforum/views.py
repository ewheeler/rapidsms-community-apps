#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4
from django.utils.translation import ugettext as _
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required

from rapidsms.webui.utils import *
from apps.smsforum.models import *
from apps.smsforum.utils import *
from apps.smsforum.forms import *
from apps.smsforum.app import CMD_MESSAGE_MATCHER
from apps.logger.models import *
# from apps.contacts.models import *
from apps.contacts.forms import GSMContactForm
from utilities.export import export

from datetime import datetime, timedelta

def index(request, template="smsforum/index.html"):
    context = {}
    if request.method == 'POST':    
        # now iterate through all the messages you learned about
        for i in request.POST.getlist('message'):
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
            if 'flagged_'+ str(id) in request.POST: flag_bool = True
            else: flag_bool = False
            note_txt = request.POST['text_'+str(id)]
            code_txt = request.POST['code_'+str(id)]
            
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
        members = village.flatten()
        village.member_count = len( members )
        last_week = ( datetime.now()-timedelta(weeks=1) )
        village.message_count = IncomingMessage.objects.filter(domain=village,received__gte=last_week).count()
    context['villages'] = paginated(request, villages)
    messages = IncomingMessage.objects.select_related().order_by('-received')
    context.update( format_messages_in_context(request, context, messages) )
    context.update( totals(context) )
    return render_to_response(request, template, context)

def format_messages_in_context(request, context, messages):
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
        context['cmd_messages'] = paginated(request, cmd_messages, per_page=5, prefix="cmd")
    if len(blast_messages)>0:
        context['blast_messages'] = paginated(request, blast_messages, per_page=10, prefix="blast")
    context['codes'] = Code.objects.filter(set=CodeSet.objects.get(name="TOSTAN_CODE"))
    return context


# TODO: move this somewhere Tostan-Specifig
# would declare this as a class but we don't need the extra database table
def SetFlag(flag):
    code = Code.objects.get(slug="True")
    flag.code = code

def IsFlag(tag):
    return tag.code.set.name == "FLAGGED_CODE"

# would declare this as a class but we don't need the extra database table
def SetCode(tag, str):
    code = Code.objects.get(slug=str)
    tag.code = code
    return tag

def village_history(request, pk, template="smsforum/history.html"):
    context = {}
    village = Village.objects.get(id=pk)
    history = MembershipLog.objects.filter(village=village).select_related('contact')
    context['village'] = village
    context['history'] = paginated(request, history)
    return render_to_response(request, template, context)

def members(request, pk, template="smsforum/members.html"):
    context = {}
    village = Village.objects.get(id=pk)
    members = village.flatten(klass=Contact)
    total_incoming_messages = 0
    total_incoming_messages_this_week = 0
    for member in members:
        connections = ChannelConnection.objects.filter(contact=member)
        if len(connections) > 0:
            # we can always click on the user to see a list of all their connections
            member.phone_number = connections[0].user_identifier
            last_week = ( datetime.now()-timedelta(weeks=1) )
            member.message_count = IncomingMessage.objects.filter(identity=member.phone_number).count()
            member.message_count_this_week = IncomingMessage.objects.filter(identity=member.phone_number,received__gte=last_week).count()
            total_incoming_messages = total_incoming_messages + member.message_count
            total_incoming_messages_this_week = total_incoming_messages_this_week + member.message_count_this_week
            member.received_message_count = OutgoingMessage.objects.filter(identity=member.phone_number).count()
        log = MembershipLog.objects.filter(contact=member,village=village).order_by('-id')
        if (log):
            member.date_joined = log[0].date
    context['village'] = village
    context['members'] = paginated(request, members)
    context['member_count'] = len(members)
    context['incoming_message_count'] = total_incoming_messages
    context['incoming_message_count_this_week'] = total_incoming_messages_this_week
    messages = IncomingMessage.objects.filter(domain=village).order_by('-received')
    format_messages_in_context(request, context, messages)
    return render_to_response(request, template, context)

def member(request, pk, template="smsforum/member.html"):
    context = {}
    contact = Contact.objects.get(id=pk)
    if request.method == "POST":
        if request.POST["message_body"]:
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
        messages = IncomingMessage.objects.filter(identity=contact.phone_number).order_by('-received')
        contact.message_count = len(messages)
        last_week = ( datetime.now()-timedelta(weeks=1) )
        last_month = ( datetime.now()-timedelta(days=30) )
        contact.message_count_this_week = IncomingMessage.objects.filter(identity=contact.phone_number,received__gte=last_week).order_by('-received').count()
        contact.message_count_this_month = IncomingMessage.objects.filter(identity=contact.phone_number,received__gte=last_month).order_by('-received').count()
        contact.received_message_count = OutgoingMessage.objects.filter(identity=contact.phone_number).count()
        # note: this defaults to the first date the member joined any community in the system
        log = MembershipLog.objects.filter(contact=contact).order_by('-id')
        if (log):
            contact.date_joined = log[0].date
        format_messages_in_context(request, context, messages)
    except ChannelConnection.DoesNotExist:
        #this is a contact without a phone number
        pass
    # if you decide to add 'date_joined', remember you need to do it for all villages
    # this person is member of
    context['member'] = contact
    return render_to_response(request, template, context)

@login_required
def edit_village(request, pk, template="smsforum/edit.html"):
    context = {}
    village = get_object_or_404(Village, id=pk)
    if request.method == "POST":
        f = VillageForm(request.POST, instance=village)
        f.save()
    context['form'] = VillageForm(instance=village)
    context['title'] = _("Edit Village")
    context['village'] = village
    return render_to_response(request, template, context)
    
@login_required
def delete_village(request, pk, template="smsforum/confirm_delete.html"):
    context = {}
    village = get_object_or_404(Village, id=pk)    
    if request.method == "POST":
        if request.POST["confirm_delete"]: # The user has already confirmed the deletion.
            #workaround for django bug. 
            #marginally useful, since we don't really want to delete the logs ever.
            logs = MembershipLog.objects.filter(village=village)
            for log in logs:
                log.village = None
                log.save()
            village.delete()
            return HttpResponseRedirect("../../villages")
    context['village'] = village
    return render_to_response(request, template, context)

def add_village(request, template="smsforum/add.html"):
    context = {}
    if request.method == 'POST':
        form = VillageForm(request.POST)
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
    return render_to_response(request, template, context)    

def totals(context):
    context['village_count'] = Village.objects.all().count()
    context['member_count'] = Contact.objects.all().count()
    context['incoming_message_count'] = IncomingMessage.objects.all().count()
    last_week = ( datetime.now()-timedelta(weeks=1) )
    context['incoming_message_count_this_week'] = IncomingMessage.objects.filter(received__gte=last_week).count()
    context['outgoing_message_count'] = OutgoingMessage.objects.all().count()
    return context

def export_village_history(request, pk, format='csv'):
    village = Village.objects.get(id=pk)
    history = MembershipLog.objects.filter(village=village)
    if request.user.is_authenticated():
        return export(history, ['id','date','node','action'])
    return export(history, ['id','date','action'])

def add_member(request, village_id=0, member_id=0, template="contacts/phone_number.html"):
    """ adding a member to a village involves either
    1. creating a new contact and adding that new contact to the village, or
    2. finding an existing contact and adding that contact to this village
    this view deals with both cases, by requiring the web user to specify
    a phone number first, and using the phone number to search for existing matches
    
    """
    context = {}
    context['title'] = _("Add Member")
    if request.method == 'POST':
        if 'phone_number_query' in request.POST:
            # we received a post of the contact's phone number
            phone_number_query = request.POST['phone_number_query'].strip()
            if phone_number_query:
                # try to find a matching contact
                try:
                    cxn = ChannelConnection.objects.get(user_identifier=phone_number_query)
                except ChannelConnection.DoesNotExist:
                    # if nothing matches, create new contact
                    form = GSMContactForm()
                    form.initial = {'phone_number':phone_number_query}
                    template="contacts/add.html"
                    context['form'] = form
                    return render_to_response(request, template, context)
                else:
                    # if contact matches, redirect to that contact's edit page
                    return HttpResponseRedirect("/village/%s/member/add/%s" % \
                                                (village_id, cxn.contact.id) )
                    # when we move to django 1.1, use the following intead:
                    # redirect(add_member, village_id, cxn.contact.id)
            else:
                context['error'] = "Please enter a phone number for member."
        else:
            # we received a post from the add/edit_member form. save()
            action = ""
            if member_id != 0:
                contact = get_object_or_404( Contact, pk=member_id )
                form = GSMContactForm(request.POST, instance=contact)
                action = "edited"
            else:
                form = GSMContactForm(request.POST)
                action = "created"
            if form.is_valid():
                c = form.save()
                context['status'] = _("Member '%(member_name)s' successfully %(action)s" % \
                                      {'member_name':c.signature, 'action':action} )
                if village_id != 0:
                    village = Village.objects.get(id=village_id)
                    village.add_children( c )
                    context['status']  = context['status'] + _(" and added to village: %s") % village.name
            else:
                context['error'] = form.errors
    if member_id != 0:
        contact = get_object_or_404(Contact, pk=member_id)
        form = GSMContactForm(instance=contact)
        context['form'] = form
        context['title'] = _("Add Member %s to village %s") % (contact.signature,village_id)
        template = "contacts/add.html"
    return render_to_response(request, template, context)

@login_required
def edit_member(request, pk, template="contacts/edit.html"):
    context = {}
    contact = get_object_or_404(Contact, id=pk)
    if request.method == "POST":
        form = GSMContactForm(request.POST, instance=contact)
        if form.is_valid():
            form.save()
            context['status'] = _("Member '%(contact_name)s' successfully updated" % \
                                {'contact_name':contact.signature} )
        else:
            context['error'] = form.errors
    else:
        form = GSMContactForm(instance=contact)
    context['form'] = form
    context['title'] = _("Edit Member") + " " + contact.signature
    context['contact'] = contact
    return render_to_response(request, template, context)
