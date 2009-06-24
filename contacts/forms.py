from django import forms
from django.forms import ModelForm
from apps.contacts.models import * 

class ContactForm(ModelForm):
     perm_send = forms.BooleanField(required=False, label="Can blast messages")
     perm_receive = forms.BooleanField(required=False, label="Can receive messages")
     perm_ignore = forms.BooleanField(required=False, label="Is spam number")    
     age = forms.IntegerField(label="Age in Years")    
     class Meta:
         model = Contact
         fields = ('given_name','family_name','gender','perm_send')

#gets/sets ContactForm with correct permissions
def GetContactForm(instance):
    form = ContactForm(instance=instance)
    form.fields['perm_send'].initial = instance.perm_send
    form.fields['perm_receive'].initial = instance.perm_receive
    form.fields['perm_ignore'].initial = instance.perm_ignore
    form.fields['age'].initial = instance.age_years
    return form

def SetContactFromPost(post, contact):
    # if no value posted, set to false
    contact = ContactForm(post, instance=contact)
    set = lambda x: x in post and True or False
    contact.perm_send = set( 'perm_send' )
    contact.perm_receive = set( 'perm_receive' )
    contact.perm_ignore = set( 'perm_ignore' )
    contact.age_years = post['age']
    contact.save()
    return contact
