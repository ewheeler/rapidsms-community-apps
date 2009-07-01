#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.db import models

from apps.reporters.models import Reporter

class Form(models.Model):
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
    word = models.SlugField(max_length=25, unique=True)
    form = models.ForeignKey(Form, blank=True, null=True)

    def __unicode__(self):
        return self.word

    def actions(self):
        return self.action_set.all()

class FormEntry(models.Model):
    reporter = models.ForeignKey(Reporter, blank=True, null=True, related_name='reporters')
    form = models.ForeignKey(Form)
    date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return "%s %s" % (self.form.description, self.date)

    @property
    def entries(self):
        return self.fieldentry_set.all()

class FieldEntry(models.Model):
    form_entry = models.ForeignKey(FormEntry)
    field = models.ForeignKey(Field)
    data = models.CharField(max_length=160, blank=True, null=True)

    def __unicode__(self):
        return "%s: %s" % (self.field.title, self.data)

class Action(models.Model):
    ACTION_TYPES = (("silent", "Silent function"),
                    ("responding", "Responding function"))
    keyword = models.ForeignKey(Keyword)
    type = models.CharField(choices=ACTION_TYPES, max_length=25)

    def __unicode__(self):
        return "%s_%s" % (self.keyword, self.type)

