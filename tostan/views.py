from rapidsms.webui.utils import render_to_response

def smscommands(request, template_name="tostan/smscommands.html"):
    return render_to_response(request, template_name)

