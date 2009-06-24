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
from apps.logger.models import *
from apps.contacts.models import *
from apps.contacts.forms import *

from datetime import datetime, timedelta

def index(req, template="smsforum/index.html"):
    context = {}
    if req.method == 'POST':
        annotations = req.POST.getlist('annotation')
        annotation_ids = req.POST.getlist('annotation_id')
        for i in range( 0, len(annotation_ids) ):
            msg = IncomingMessage.objects.get( id=annotation_ids[i] )
            if msg.annotation != annotations[i]:
                msg.annotation = annotations[i]
                msg.save()
    villages = Village.objects.all()
    for village in villages:
        # once this site bears more load, we can replace flatten() with village.subnodes
        # and stop reporting num_messages
        village.member_count = len( village.flatten() )
        last_week = ( datetime.now()-timedelta(weeks=1) )
        village.message_count = IncomingMessage.objects.filter(domain=village,received__gte=last_week).count()
        village.messages_sent_count = village.message_count * village.member_count
    context['villages'] = paginated(req, villages)
    messages = IncomingMessage.objects.all().order_by('-received')
    context['messages'] = paginated(req, messages)
    return render_to_response(req, template, context)
    
    #change this to a generic view!
    """
    communities = Community.objects.all()
    for community in communities:
        # once this site bears more load, we can replace flatten() with village.subnodes
        # and stop reporting num_messages
        community.member_count = len( village.flatten() )
        last_week = ( datetime.now()-timedelta(weeks=1) )
        community.message_count = IncomingMessage.objects.filter(domain=community,received__gte=last_week).count()
        community.messages_sent_count = community.message_count * community.member_count    
    context['communities'] = paginated(req, communities)
    #messages sent this week
    return render_to_response(req, template, context)
    """

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
    context['messages'] = paginated(req, messages)
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
    except ChannelConnection.DoesNotExist:
        pass
    last_week = ( datetime.now()-timedelta(weeks=1) )
    messages = IncomingMessage.objects.filter(identity=contact.phone_number,received__gte=last_week).order_by('-received')
    contact.message_count = len(messages)
    context['member'] = contact
    context['messages'] = paginated(req, messages)
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
        form = SetContactFromPost(req.POST, contact)
    else:
        form = GetContactForm(instance=contact)
    context['form'] = form
    context['title'] = _("Edit Member")
    return render_to_response(req, template, context)

def add_community(req, template="smsforum/add.html"):
    context = {}
    if req.method == 'POST':        
        form = AddCommunityForm(req.POST)        
        if form.is_valid():
            c = Community(name=form.cleaned_data['name'])
            c.save()
            print form.cleaned_data['members']
            pass
    context['form'] = AddCommunityForm()
    context['title'] = _("Add Community")
    return render_to_response(req, template, context)


    


"""
@require_http_methods(["GET", "POST"])  
def edit_reporter(req, pk):
    rep = get_object_or_404(Contact, pk=pk)
    
    def get(req):
        return render_to_response(req,
            "reporters/reporter.html", {
                
                # display paginated reporters in the left panel
                "reporters": paginated(req, Contact.objects.all()),
                
                # list all groups + backends in the edit form
                "all_groups": ReporterGroup.objects.flatten(),
                "all_backends": PersistantBackend.objects.all(),
                
                # split objects linked to the editing reporter into
                # their own vars, to avoid coding in the template
                "connections": rep.connections.all(),
                "groups":      rep.groups.all(),
                "reporter":    rep })
    
    @transaction.commit_manually
    def post(req):
        
        # if DELETE was clicked... delete
        # the object, then and redirect
        if req.POST.get("delete", ""):
            pk = rep.pk
            rep.delete()
            
            transaction.commit()
            return message(req,
                "Contact %d deleted" % (pk),
                link="/reporters")
                
        else:
            # check the form for errors (just
            # missing fields, for the time being)
            errors = check_reporter_form(req)
            
            # if any fields were missing, abort. this is
            # the only server-side check we're doing, for
            # now, since we're not using django forms here
            if errors["missing"]:
                transaction.rollback()
                return message(req,
                    "Missing Field(s): %s" %
                        ", ".join(errors["missing"]),
                    link="/reporters/%s" % (rep.pk))
            
            try:
                # automagically update the fields of the
                # reporter object, from the form
                update_via_querydict(rep, req.POST).save()
                update_reporter(req, rep)
                
                # no exceptions, so no problems
                # commit everything to the db
                transaction.commit()
                
                # full-page notification
                return message(req,
                    "Contact %d updated" % (rep.pk),
                    link="/reporters")
            
            except Exception, err:
                transaction.rollback()
                raise
        
    # invoke the correct function...
    # this should be abstracted away
    if   req.method == "GET":  return get(req)
    elif req.method == "POST": return post(req)


def message(req, msg, link=None):
    return render_to_response(req,u
        "message.html", {
            "message": msg,
            "link": link
    })

def check_reporter_form(req):
    
    # verify that all non-blank
    # fields were provided
    missing = [
        field.verbose_name
        for field in Contact._meta.fields
        if req.POST.get(field.name, "") == ""
           and field.blank == False]
    
    # TODO: add other validation checks,
    # or integrate proper django forms
    return {
        "missing": missing }


def update_reporter(req, rep):
    
    # as default, we will delete all of the connections
    # and groups from this reporter. the loops will drop
    # objects that we SHOULD NOT DELETE from these lists
    del_conns = list(rep.connections.values_list("pk", flat=True))
    del_grps = list(rep.groups.values_list("pk", flat=True))


    # iterate each of the connection widgets from the form,
    # to make sure each of them are linked to the reporter
    connections = field_bundles(req.POST, "conn-backend", "conn-identity")
    for be_id, identity in connections:
        
        # skip this pair if either are missing
        if not be_id or not identity:
            continue
        
        # create the new connection - this could still
        # raise a DoesNotExist (if the be_id is invalid),
        # or an IntegrityError or ValidationError (if the
        # identity or report is invalid)
        conn, created = PersistantConnection.objects.get_or_create(
            backend=PersistantBackend.objects.get(pk=be_id),
            identity=identity)
        
        # update the reporter separately, in case the connection
        # exists, and is already linked to another reporter
        conn.reporter = rep
        conn.save()
        
        # if this conn was already
        # linked, don't delete it!
        if conn.pk in del_conns:
            del_conns.remove(conn.pk)


    # likewise for the group objects
    groups = field_bundles(req.POST, "group")	
    for grp_id, in groups:
        
        # skip this group if it's empty
        # (an empty widget is displayed as
        # default, which may be ignored here)
        if not grp_id:
            continue
        
        # link this group to the reporter
        grp = ReporterGroup.objects.get(pk=grp_id)
        rep.groups.add(grp)
        
        # if this group was already
        # linked, don't delete it!
        if grp.pk in del_grps:
            del_grps.remove(grp.pk)
    
    
    # delete all of the connections and groups 
    # which were NOT in the form we just received
    rep.connections.filter(pk__in=del_conns).delete()
    rep.groups.filter(pk__in=del_grps).delete()


@require_http_methods(["GET", "POST"])
def add_reporter(req):
    def get(req):
        
        # maybe pre-populate the "connections" field
        # with a connection object to convert into a
        # reporter, if provided in the query string
        connections = []
        if "connection" in req.GET:
            connections.append(
                get_object_or_404(
                    PersistantConnection,
                    pk=req.GET["connection"]))
        
        return render_to_response(req,
            "reporters/reporter.html", {
                
                # display paginated reporters in the left panel
                "reporters": paginated(req, Contact.objects.all()),
                
                # maybe pre-populate connections
                "connections": connections,
                
                # list all groups + backends in the edit form
                "all_groups": ReporterGroup.objects.flatten(),
                "all_backends": PersistantBackend.objects.all() })

    @transaction.commit_manually
    def post(req):
        
        # check the form for errors
        errors = check_reporter_form(req)
        
        # if any fields were missing, abort. this is
        # the only server-side check we're doing, for
        # now, since we're not using django forms here
        if errors["missing"]:
            transaction.rollback()
            return message(req,
                "Missing Field(s): %s" %
                    ", ".join(missing),
                link="/reporters/add")
        
        try:
            # create the reporter object from the form
            rep = insert_via_querydict(Contact, req.POST)
            rep.save()
            
            # every was created, so really
            # save the changes to the db
            update_reporter(req, rep)
            transaction.commit()
            
            # full-page notification
            return message(req,
                "Contact %d added" % (rep.pk),
                link="/reporters")
        
        except Exception, err:
            transaction.rollback()
            raise
    
    # invoke the correct function...
    # this should be abstracted away
    if   req.method == "GET":  return get(req)
    elif req.method == "POST": return post(req)




@require_http_methods(["GET", "POST"])
def add_group(req):
    if req.method == "GET":
        return render_to_response(req,
            "reporters/group.html", {
                "all_groups": ReporterGroup.objects.flatten(),
                "groups": paginated(req, ReporterGroup.objects.flatten()) })
        
    elif req.method == "POST":
        
        # create a new group using the flat fields,
        # then resolve and update the parent group
        # TODO: resolve foreign keys in i_via_q
        grp = insert_via_querydict(ReporterGroup, req.POST)
        parent_id = req.POST.get("parent_id", "")
        if parent_id:
            grp.parent = get_object_or_404(
                ReporterGroup, pk=parent_id)
        
        grp.save()
        
        return message(req,
            "Group %d added" % (grp.pk),
            link="/reporters")


@require_http_methods(["GET", "POST"])
def edit_group(req, pk):
    grp = get_object_or_404(ReporterGroup, pk=pk)
    
    if req.method == "GET":
        
        # fetch all groups, to be displayed
        # flat in the "parent group" field
        all_groups = ReporterGroup.objects.flatten()
        
        # iterate the groups, to mark one of them
        # as selected (the editing group's parent)
        for this_group in all_groups:
            if grp.parent == this_group:
                this_group.selected = True
        
        return render_to_response(req,
            "reporters/group.html", {
                "groups": paginated(req, ReporterGroup.objects.flatten()),
                "all_groups": all_groups,
                "group": grp })
    
    elif req.method == "POST":
        # if DELETE was clicked... delete
        # the object, then and redirect
        if req.POST.get("delete", ""):
            pk = grp.pk
            grp.delete()
            
            return message(req,
                "Group %d deleted" % (pk),
                link="/reporters")

        # otherwise, update the flat fields of the group
        # object, then resolve and update the parent group
        # TODO: resolve foreign keys in u_via_q
        else:
            update_via_querydict(grp, req.POST)
            parent_id = req.POST.get("parent_id", "")
            if parent_id:
                grp.parent = get_object_or_404(
                    ReporterGroup, pk=parent_id)
            
            # if no parent_id was passed, we can assume
            # that the field was cleared, and remove it
            else: grp.parent = None
            grp.save()
            
            return message(req,
                "Group %d saved" % (grp.pk),
                link="/reporters")
"""
