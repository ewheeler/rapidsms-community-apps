from django import forms
from django.forms import ModelForm
from apps.contacts.models import * 

class ContactForm(ModelForm):
     perm_send = forms.BooleanField(required=False, label="Can blast messages")
     perm_receive = forms.BooleanField(required=False, label="Can receive messages")
     perm_ignore = forms.BooleanField(required=False, label="Is spam number")    
     age = forms.IntegerField(required=False, label="Age in Years")    
     phone_number = forms.IntegerField(required=False, label="Phone Number")    
     communication_channel = forms.ModelChoiceField(CommunicationChannel.objects, required=False)    
     class Meta:
         model = Contact
         fields = ('common_name','given_name','family_name','gender')

#gets/sets ContactForm with correct permissions
def get_contact_form(instance):
    form = ContactForm(instance=instance)
    form.fields['perm_send'].initial = instance.perm_send
    form.fields['perm_receive'].initial = instance.perm_receive
    form.fields['perm_ignore'].initial = instance.perm_ignore
    form.fields['age'].initial = instance.age_years
    form.fields['phone_number'].initial = instance.age_years
    conns = ChannelConnection.objects.filter(contact=instance)
    if len(conns)>0: form.fields['phone_number'].initial = conns[0].user_identifier
    return form

# doesn't check for whether this contact exists already
def create_contact_from_post(post, contact):
    # if no value posted, set to false
    contact = ContactForm(post, instance=contact)
    set = lambda x: x in post and True or False
    contact.perm_send = set( 'perm_send' )
    contact.perm_receive = set( 'perm_receive' )
    contact.perm_ignore = set( 'perm_ignore' )
    contact.age_years = post['age']
    c = contact.save()
    if len(post['phone_number'])>0 and len( post['communication_channel']>0 ): 
        conn = ChannelConnection( user_identifier=post['phone_number'], \
                                  communication_channel=contact.cleaned_data['communication_channel'], \
                                  contact=c )
        conn.save()
    return contact
