#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models

from reporters.models import Reporter

class Form(models.Model):
    """ Collection of fields defining data to be collected. """
    description = models.CharField(max_length=160)

    def __unicode__(self):
        return self.description 

    @property
    def keyword(self):
        return self.keyword_set.all()[0]

    @property
    def fields(self):
        return self.field_set.all()

    @property
    def entries(self):
        return self.formentry_set.all()

class Field(models.Model):
    """ Data fields for a form """
    DATA_TYPES = (("float", "Number"),
                  ("str",   "Any word"),
                  ("bool",  "Yes/No"))

    form = models.ForeignKey(Form)
    title = models.SlugField(max_length=25)
    description = models.CharField(max_length=40)
    data_type = models.CharField(choices=DATA_TYPES, max_length=5)

    def __unicode__(self):
        return self.title

    class Meta:
        order_with_respect_to = "form"

    @property
    def entries(self):
        return self.fieldentry_set.all()

class Keyword(models.Model):
    """ The Keyword is the central model of this app. Keywords can be defined to
        trigger actions, indicate a form, or both. A keyword can have only one form,
        but many actions may be associated with a single keyword. """
    word = models.SlugField(max_length=25, unique=True)
    form = models.ForeignKey(Form, blank=True, null=True)

    def __unicode__(self):
        return self.word

    def actions(self):
        return self.action_set.all()

class FormEntry(models.Model):
    """ User-submitted form entries. """
    reporter = models.ForeignKey(Reporter, blank=True, null=True, related_name='reporters')
    form = models.ForeignKey(Form)
    date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s %s" % (self.form.description, self.date)

    @property
    def entries(self):
        return self.fieldentry_set.all()

class FieldEntry(models.Model):
    """ User-submitted data. """
    form_entry = models.ForeignKey(FormEntry)
    field = models.ForeignKey(Field)
    data = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return "%s: %s" % (self.field.title, self.data)

class Action(models.Model):
    """ A keyword's actions are executed whenever a message is received that
        contains the keyword. Actions may or may not respond to the message
        sender, so there are two possible types of actions: silent (actions that
        do not send a response to sender) and responding (actions that do send a
        response to the sender). 
        Actions are defined in the actions.py file. 
        TODO: This whole actions model/concept is half-baked. 
        When/if it is used for a project, these actions will need to be revisited. 
        Note: another kind of action exists: formactions, which would be called
        after a successful form entry, and are always silent. See actions.py for
        all of the exciting details. """
    ACTION_TYPES = (("silent", "Silent function"),
                    ("responding", "Responding function"))
    keyword = models.ForeignKey(Keyword)
    type = models.CharField(choices=ACTION_TYPES, max_length=25)

    def __unicode__(self):
        return "%s_%s" % (self.keyword, self.type)

