from django import forms
from django.forms import ModelForm
from apps.contacts.models import *
from django.db import transaction

class BasicContactForm(ModelForm):
    perm_send = forms.BooleanField(required=False, label="Can blast messages")
    perm_receive = forms.BooleanField(required=False, label="Can receive messages")
    perm_ignore = forms.BooleanField(required=False, label="Is spam number")    
    age_years = forms.IntegerField(required=False, label="Age in Years")
    
    class Meta:
        model = Contact
        fields = ('common_name','given_name','family_name','gender')
   
    def __init__(self, data=None, instance=None):
        super(BasicContactForm, self).__init__(data=data, instance=instance)
        if data is not None:
            set = lambda x: x in data and True or False
            self.fields['perm_send'].value = set( 'perm_send' )
            self.fields['perm_receive'].value = set( 'perm_receive' )
            self.fields['perm_ignore'].value = set( 'perm_ignore' )
            self.fields['age_years'].value = data['age_years']
        if instance is not None:
            self.fields['perm_send'].initial = instance.perm_send
            self.fields['perm_receive'].initial = instance.perm_receive
            self.fields['perm_ignore'].initial = instance.perm_ignore
            self.fields['age_years'].initial = instance.age_years

    @transaction.commit_on_success
    def save(self, force_insert=False, force_update=False, commit=True):
        m = super(BasicContactForm, self).save(commit=False)
        m.perm_send = self.fields['perm_send'].value
        m.perm_receive = self.fields['perm_receive'].value
        m.perm_ignore = self.fields['perm_ignore'].value
        if self.fields['age_years'].value:
            m.age_years = float( self.fields['age_years'].value )
        if commit:
            m.save()
        return m

class ContactWithChannelForm(BasicContactForm):
    phone_number = forms.IntegerField(required=False, label="Phone Number")
    communication_channel = forms.ModelChoiceField(CommunicationChannel.objects, required=False)
     
    def __init__(self, data=None, instance=None):
        super(ContactWithChannelForm, self).__init__(data=data, instance=instance)
        conns = ChannelConnection.objects.filter(contact=instance)
        if conns:
            self.fields['phone_number'].initial = conns[0].user_identifier
            self.fields['communication_channel'].initial = conns[0].communication_channel
    
    @transaction.commit_on_success
    def save(self):
        contact = super(ContactWithChannelForm, self).save()
        if 'phone_number' in self.cleaned_data and self.cleaned_data['phone_number']:
            conns = ChannelConnection.objects.filter(contact=contact)
            if not conns:
                conn = ChannelConnection( contact=contact )
            else:
                conn = conns[0]
            conn.user_identifier=self.cleaned_data['phone_number']
            if 'communication_channel' not in self.cleaned_data or not self.cleaned_data['communication_channel']:
                raise ValueError("If you specify phone number, you must also add communication channel")
            conn.communication_channel=self.cleaned_data['communication_channel']
            conn.save()
        else:
            conns = ChannelConnection.objects.filter(contact=contact)
            if conns: conns.delete()            
        return contact

    def clean(self):
         cleaned_data = self.cleaned_data
         if 'phone_number' in cleaned_data and cleaned_data['phone_number']: 
             if 'communication_channel' not in cleaned_data or not cleaned_data['communication_channel']:
                 # don't need to set the communication channel if there is only one in the system
                 raise forms.ValidationError("If you specify phone number, you must also add communication channel")
         return cleaned_data;

class GSMContactForm(BasicContactForm):
    phone_number = forms.IntegerField(required=False, label="Phone Number")
    communication_channel = None

    def __init__(self, data=None, instance=None):
        super(GSMContactForm, self).__init__(data=data, instance=instance)
        conns = ChannelConnection.objects.filter(contact=instance)
        if conns:
            self.fields['phone_number'].initial = conns[0].user_identifier

    @transaction.commit_on_success
    def save(self):
        contact = super(GSMContactForm, self).save()
        # keep default channelconnection
        # unless none exists, in which case create default one
        if 'phone_number' in self.cleaned_data and self.cleaned_data['phone_number']:
            # this is rather hack-ish
            channel = CommunicationChannel.objects.get(backend_slug__icontains='gsm')
            conns = ChannelConnection.objects.filter(contact=contact, communication_channel=channel)
            if not conns:
                conn = ChannelConnection( contact=contact, communication_channel=channel )
            else:
                conn = conns[0]
            conn.user_identifier=self.cleaned_data['phone_number']
            conn.save()
        return contact
