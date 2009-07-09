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
    
     def clean(self):
         cleaned_data = self.cleaned_data
         if 'phone_number' in cleaned_data and cleaned_data['phone_number']>0: 
             if cleaned_data['communication_channel'] is None:
                 # don't need to set the communication channel if there is only one in the system
                 raise forms.ValidationError("If you specify phone number, you must also add communication channel")
         return cleaned_data;
     
     def save(self):
        contact = super(ContactForm, self).save()
        if 'phone_number' in self.cleaned_data and self.cleaned_data['phone_number']>0: 
            conns = ChannelConnection.objects.filter(contact=contact)
            if len(conns) == 0:
                conn = ChannelConnection( contact=contact )
            else:
                conn = conns[0]
            conn.user_identifier=self.cleaned_data['phone_number']
            if self.cleaned_data['communication_channel'] is None:
                 raise forms.ValueError("If you specify phone number, you must also add communication channel")
            conn.communication_channel=self.cleaned_data['communication_channel']
            conn.save()
        return contact

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
    if not contact.is_valid():
        return contact
    contact.save()
    return contact
