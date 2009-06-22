from rapidsms.webui.utils import render_to_response
from django.contrib.auth.decorators import login_required, permission_required
from models import *

@login_required
@permission_required("harvard.can_view")
def index(req):
    template_name="harvard/index.html"
    
    # will store number of sucesses, failures per user
    totals = { "A" : 0, "C" : 0, "F" : 0, "total" : 0, "tries" : 0}
    status_counts = { }
    surveys = HarvardReport.objects.all().order_by("started").order_by("reporter__alias")
    for survey in surveys:
        if not survey.reporter.alias in status_counts:
            status_counts[survey.reporter.alias] = {"A" : 0, 
                                                    "C" : 0, 
                                                    "F" : 0, 
                                                    "total" : 0, 
                                                    "tries" : 0}
        status_counts[survey.reporter.alias][survey.status] += 1
        status_counts[survey.reporter.alias]["total"] += 1
        status_counts[survey.reporter.alias]["tries"] += survey.num_tries
        totals[survey.status] += 1
        totals["total"] += 1
        totals["tries"] += survey.num_tries
        survey.question = get_display_question(survey.session.tree)
        survey.child = "child" in survey.session.tree.trigger
    if status_counts:
        totals["avg_tries"] = float(totals["tries"]) / float(totals["total"])
        for user in status_counts:
            status_counts[user]["avg_tries"] =\
                float(status_counts[user]["tries"])\
                / float(status_counts[user]["total"])
    
    return render_to_response(req, template_name, 
                              {"status_counts" : status_counts, 
                               "totals" : totals,
                               "surveys" : surveys
                               })

def get_display_question(tree):
    if "1" in tree.trigger: 
        return "missed 7 days"
    elif "2" in tree.trigger: 
        return "missed 30 days"
    elif "3" in tree.trigger: 
        return "missed since last visit"
    return None