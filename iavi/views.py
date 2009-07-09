from rapidsms.webui.utils import render_to_response
from models import *
from forms import *
from datetime import datetime, timedelta
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.forms import AdminPasswordChangeForm


@login_required
@permission_required("iavi.can_view")
def index(req):
    template_name="iavi/index.html"
    return render_to_response(req, template_name, {})

@login_required
@permission_required("iavi.can_view")
def compliance(req):
    template_name="iavi/compliance.html"
    
    user = req.user
    try:
        profile = user.get_profile()
        locations = profile.locations.all()
    except IaviProfile.DoesNotExist:
        # if they don't have a profile they aren't associated with
        # any locations and therefore can't view anything.  Only
        # exceptions are the superusers
        if user.is_superuser:
            locations = Location.objects.all()
        else:
            return render_to_response(req, "iavi/no_profile.html", {})
    
    reporters = IaviReporter.objects.filter(location__in=locations).order_by('alias')
    seven_days = timedelta(days=7)
    thirty_days = timedelta(days=30)
    tomorrow = datetime.today() + timedelta(days=1)
    for reporter in reporters:
        
        all_reports = Report.objects.filter(reporter=reporter)
        last_7 = all_reports.filter(started__gte=tomorrow-seven_days)
        last_30 = all_reports.filter(started__gte=tomorrow-thirty_days)
        
        reporter.all_reports = len(all_reports)
        reporter.all_compliant = len(all_reports.filter(status="F"))
        if reporter.all_reports != 0:
            reporter.all_ratio = float(reporter.all_compliant) / float(reporter.all_reports)
            reporter.all_flag = _get_flag(reporter.all_ratio)
                
        
        reporter.past_7_reports = len(last_7)
        reporter.past_7_compliant = len(last_7.filter(status="F"))
        if reporter.past_7_reports != 0:
            reporter.past_7_ratio = float(reporter.past_7_compliant) /float(reporter.past_7_reports)  
            reporter.past_7_flag = _get_flag(reporter.past_7_ratio)
            
        reporter.past_30_reports = len(last_30)
        reporter.past_30_compliant = len(last_30.filter(status="F"))
        if reporter.past_30_reports != 0:
            reporter.past_30_ratio = float(reporter.past_30_compliant) /float(reporter.past_30_reports)  
            reporter.past_30_flag = _get_flag(reporter.past_30_ratio)
            
    return render_to_response(req, template_name, {"reporters":reporters })

@login_required
@permission_required("iavi.can_see_data")
def data(req):
    template_name="iavi/data.html"
    user = req.user
    try:
        profile = user.get_profile()
        locations = profile.locations.all()
    except IaviProfile.DoesNotExist:
        # if they don't have a profile they aren't associated with
        # any locations and therefore can't view anything.  Only
        # exceptions are the superusers
        if user.is_superuser:
            # todo: allow access to everything
            locations = Location.objects.all()
        else:
            return render_to_response(req, "iavi/no_profile.html", { } )
    
    seven_days = timedelta(days=7)
    #thirty_days = timedelta(days=30)
    tomorrow = datetime.today() + timedelta(days=1)
    
    kenya_reports = KenyaReport.objects.filter(started__gte=tomorrow-seven_days).filter(reporter__location__in=locations).order_by("-started")
    uganda_reports = UgandaReport.objects.filter(started__gte=tomorrow-seven_days).filter(reporter__location__in=locations).order_by("-started")
    return render_to_response(req, template_name, {"kenya_reports":kenya_reports, "uganda_reports":uganda_reports})

@login_required
@permission_required("iavi.is_admin")
def users(req):
    template_name="iavi/users.html"
    current_user = req.user
    try:
        profile = current_user.get_profile()
        locations = profile.locations.all()
    except IaviProfile.DoesNotExist:
        # if they don't have a profile they aren't associated with
        # any locations and therefore can't view anything.  Only
        # exceptions are the superusers
        if current_user.is_superuser:
            # todo: allow access to everything
            locations = Location.objects.all()
        else:
            return render_to_response(req, "iavi/no_profile.html", {})
    
    all_users = User.objects.all()
    for user in all_users:
        try:
            profile = user.get_profile()
            # set some fields in the user object so we can access them in the template
            location_strings = [str(location) for location in profile.locations.all()]
            user.locations = ", ".join(location_strings)
        except IaviProfile.DoesNotExist:
            user.locations = ""
        if user.is_superuser:
            user.permission_string = "Administrator"
        else: 
            user.permission_string = ", ".join([str(group) for group in user.groups.all()])
        
    return render_to_response(req, template_name, { "all_users" : all_users })


@login_required
@permission_required("iavi.is_admin")
def user_edit(req, id):
    user_to_edit = User.objects.get(id=id)
    try:
        profile = user_to_edit.get_profile()
    except IaviProfile.DoesNotExist:
        profile = None
    if req.method == 'POST': 
        user_form = UserForm(req.POST, instance=user_to_edit) 
        profile_form = IaviProfileForm(req.POST, instance=profile) 
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            if user.is_superuser:
                # make sure any super user is also staff so they
                # can easily change passwords
                user.is_staff = True;
                
                user.save()
            
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            profile_form.save_m2m()
            return HttpResponseRedirect('/iavi/users')
    else:
        user_form =  UserForm(instance=user_to_edit)
        profile_form = IaviProfileForm(instance=profile)
    template_name="iavi/user_edit.html"
    return render_to_response(req, template_name, {"current_user" : user_to_edit,
                                                   "user_form" : user_form,
                                                   "profile_form" : profile_form })

@login_required
@permission_required("iavi.is_admin")
def new_user(req):
    if req.method == 'POST': 
        user_form = UserForm(req.POST)
        profile_form = IaviProfileForm(req.POST)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            if user.is_superuser:
                # make sure any super user is also staff so they
                # can easily change passwords through the admin
                user.is_staff = True;
                user.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            profile_form.save_m2m()
            return HttpResponseRedirect('/iavi/users')
    else:
        user_form =  UserForm()
        profile_form = IaviProfileForm()
    template_name="iavi/user_edit.html"
    return render_to_response(req, template_name, {"user_form" : user_form,
                                                   "profile_form" : profile_form })



def password_change(req, id):
    user_to_edit = User.objects.get(id=id)
    if req.method == 'POST': 
        password_form = AdminPasswordChangeForm(user_to_edit, req.POST)
        if password_form.is_valid():
            password_form.save()
            return HttpResponseRedirect('/iavi/users/%s/edit' % user_to_edit.id)
    else:
        password_form = AdminPasswordChangeForm(user_to_edit)
    template_name="iavi/password_change.html"
    return render_to_response(req, template_name, {"current_user" : user_to_edit,
                                                   "form" : password_form})
    
    

@login_required
@permission_required("iavi.can_read_participants")
def participants(req):
    template_name="iavi/participants.html"
    user = req.user
    try:
        profile = user.get_profile()
        locations = profile.locations.all()
    except IaviProfile.DoesNotExist:
        # if they don't have a profile they aren't associated with
        # any locations and therefore can't view anything.  Only
        # exceptions are the superusers
        if user.is_superuser:
            locations = Location.objects.all()
        else:
            return render_to_response(req, "iavi/no_profile.html", {})
    
    parts = StudyParticipant.objects.filter(reporter__location__in=locations).order_by('reporter__alias')
    return render_to_response(req, template_name, {"participants" : parts})


@login_required
@permission_required("iavi.can_read_participants")
def participant_summary(req, id):
    template_name="iavi/participant_summary.html"
    try:
        reporter = IaviReporter.objects.get(pk=id)
        data = StudyParticipant.objects.get(reporter=reporter)
        reporter.start_date = data.start_date 
        reporter.end_date = data.end_date 
    except IaviReporter.DoesNotExist:
        reporter = None
    except StudyParticpant.DoesNotExist:
        # no study data, this is okay, the fields will just show up blank
        pass 
    # todo - see if we want to put these back in
    kenya_reports = KenyaReport.objects.filter(reporter=reporter).order_by("-started")
    uganda_reports = UgandaReport.objects.filter(reporter=reporter).order_by("-started")
    return render_to_response(req, template_name, {"reporter" : reporter,"kenya_reports":kenya_reports, "uganda_reports":uganda_reports})

@login_required
@permission_required("iavi.can_write_participants")
def participant_edit(req, id):
    reporter = IaviReporter.objects.get(pk=id)
    if req.method == 'POST': 
        form = IaviReporterForm(req.POST) 
        if form.is_valid():
            # Process the data in form.cleaned_data
            id = req.POST["reporter_id"]
            if not id: 
                # should puke.  should also not be possible through the UI
                raise Exception("Reporter ID not set in form.  How did you get here?")
            reporter = IaviReporter.objects.get(id=id)
            reporter.pin = form.cleaned_data["pin"]
            reporter.location = form.cleaned_data["location"]
            reporter.alias = IaviReporter.get_alias(reporter.location.code, form.cleaned_data["participant_id"])
            reporter.save()
            conn = reporter.connection() 
            conn.identity = form.cleaned_data["phone"]
            conn.save()
            end_date = form.cleaned_data["end_date"]
            try:
                participant = StudyParticipant.objects.get(reporter=reporter)
                participant.end_date = end_date
                participant.save()
            except StudyParticipant.DoesNotExist:
                # nothing to do with the end date
                pass
            return HttpResponseRedirect('/iavi/participants/%s/' % id) 
    else:
        try:
            reporter = IaviReporter.objects.get(pk=id)
            try:
                study_data = StudyParticipant.objects.get(reporter=reporter)
                reporter.end_date = study_data.end_date
            except StudyParticipant.DoesNotExist:
                reporter.end_date = None
            if reporter.location:
                form = IaviReporterForm(initial={"participant_id" :reporter.study_id, "location" : reporter.location.pk,
                                                 "pin" : reporter.pin, "phone" : reporter.connection().identity, 
                                                 "end_date" : reporter.end_date } )
            else: 
                form = IaviReporterForm({"participant_id" :reporter.study_id, 
                                         "pin" : reporter.pin, "phone" : reporter.connection().identity, 
                                         "end_date" : reporter.end_date } )
        except IaviReporter.DoesNotExist:
            form = IaviReporterForm()

    template_name="iavi/participant_edit.html"
    return render_to_response(req, template_name, {"form" : form, "reporter" : reporter})


@login_required
@permission_required("iavi.can_write_participants")
def participant_delete(req, id):
    template_name="iavi/participant_delete.html"
    num_reports = 0
    try:
        reporter = IaviReporter.objects.get(pk=id)
        num_reports = len(Report.objects.filter(reporter=reporter))
    except IaviReporter.DoesNotExist:
        reporter = None
    if req.method == 'POST': 
        if reporter:
            reporter.delete()
        reporter = None
    return render_to_response(req, template_name, {"reporter" : reporter, "num_reports" : num_reports})

def _get_flag(ratio):
    if ratio <= .6:
        return "severe"
    elif ratio <= .75:
        return "warning"
    return "good"
            