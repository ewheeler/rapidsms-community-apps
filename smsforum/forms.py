from django import forms
from django.forms import ModelForm
from apps.smsforum.models import *
from apps.contacts.models import * 

# On this page, users can upload an xsd file from their laptop
# Then they get redirected to a page where they can download the xsd

class VillageForm(ModelForm):
    class Meta:
        model = Village
        fields = ('name')

"""    
class AddCommunityForm(forms.Form):
    name = forms.CharField(label=u'Name of Community')
    members = forms.ModelMultipleChoiceField(Village.objects, label=u'Add Villages')
"""
