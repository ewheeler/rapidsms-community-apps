from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from rapidsms.webui.utils import render_to_response

from quickforms.models import Keyword

def index(req):
    return render_to_response(req, "quickforms/index.html", 
        { "keywords" : Keyword.objects.all() })
