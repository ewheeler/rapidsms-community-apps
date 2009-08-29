#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.views.decorators.http import require_GET, require_http_methods
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse

from rapidsms.webui.utils import render_to_response, paginated
from apps.reporters.utils import insert_via_querydict, update_via_querydict
from models import *


def __global(req):
    return {
        "all_data": INFSSS.objects.all() }


def message(req, msg, link=None):
    return render_to_response(req,
        "message.html", {
            "message": msg,
            "link": link
    })



@require_GET
def view_all_gmc(req):
    return render_to_response(req,
        "malawihealth/dashboard.html", {
            "all_gmc": GMC.objects.all() })

@require_GET
def dashboard(req):
    return render_to_response(req,
        "malawihealth/dashboard.html", {
            "all_data": INFSSS.objects.all() })

@require_GET
def view_all_data(req):
    return render_to_response(req,
        "malawihealth/dashboard.html", {
            "all_data": INFSSS.objects.all() })

@require_GET
def view_all_patients(req):
    return render_to_response(req,
        "malawihealth/dashboard.html", {
            "all_patients": Patient.objects.all() })

@require_GET
def view_by_date_range(req,d1,d2):
    return render_to_response(req,
        "malawihealth/dashboard.html", {
            "all_data": INFSSS.objects.all() })
