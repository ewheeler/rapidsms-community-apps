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
        "nutrition": Nutrition.objects.all() }

@require_GET
def dashboard(req):
    return render_to_response(req,
        "nutrition/dashboard.html", {
            "all_nutrition": Nutrition.objects.all()})
            #"all_wasting": WastingTable.objects.all(),
            #"all_stunting": StuntingTable.objects.all(),
            #"all_locrep": LocationReporter.objects.all() })


