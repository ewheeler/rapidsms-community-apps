from django import forms
from django.forms import ModelForm
from apps.smsforum.models import *
from apps.contacts.models import * 

# On this page, users can upload an xsd file from their laptop
# Then they get redirected to a page where they can download the xsd
"""class AddVillage(forms.Form):
    name = forms.CharField()
    file  = forms.FileField()
    form_display_name= forms.CharField(max_length=128, label=u'Form Display Name')
"""

class VillageForm(ModelForm):
     class Meta:
         model = Village
         fields = ('name')
    
class ContactForm(ModelForm):
     class Meta:
         model = Contact
         fields = ('given_name','family_name','gender','age_months')
    
class AddCommunityForm(forms.Form):
    name = forms.CharField(label=u'Name of Community')
    members = forms.ModelMultipleChoiceField(Village.objects, label=u'Add Villages')

