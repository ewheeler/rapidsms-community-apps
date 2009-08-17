#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django.db import models
from apps.reporters.models import Reporter
from apps.locations.models import Location


class PersonType(models.Model):
    singular = models.CharField(max_length=100, unique=True)
    plural   = models.CharField(max_length=100, unique=True)


    class Meta:
        verbose_name = "Type"

    def __unicode__(self):
        return self.title


    @property
    def title(self):
        """Returns the singular form of this PersonType.
           This is only here for consistency, because most
           models have a "title" field."""
        return self.singular


class Person(models.Model):
    GENDER_CHOICES = (
        ("M", "Male"),
        ("F", "Female"))

    # this isn't a GUID. many deployments use short
    # codes (#1-60 for each GMC (location) in malawi),
    # so many kids share codes. for this reason, to
    # find a Person via their code, see Person.lookup
    code = models.CharField(max_length=30, blank=True)

    # people can be "owned" by locations or reporters,
    # to make it practical to look them up with context.
    # (eg, if a linked reporter makes a report on "adam",
    # or "1", we can take a guess at who they mean without
    # requiring a GUID for every child)
    location = models.ManyToManyField(Location, related_name="people", blank=True)
    reporter = models.ManyToManyField(Reporter, related_name="people", blank=True)

    # this field is deliberately dumb, to avoid the
    # unsolvable problem of parsing human names into
    # their components, and knowing how to refer to a
    # person correctly (and politely)
    name = models.CharField(max_length=100, blank=True)

    # children can be marked as "inactive" by setting this
    # False, to leave them in the system while allowing their
    # code and/or name to be reused without ambiguity
    active = models.BooleanField(default=True)

    # i can't imagine any situaton where a Person could
    # be of multiple Types, but there's no reason not to
    #types = models.ManyToManyField(PersonType, related_name="people", blank=True)

    # ...actually, yes there is.
    # YAGNI. aren't you guys proud?
    type = models.ForeignKey(PersonType)


    # and now, back to our regularly-scheduled
    # programming (ha!). all of these common fields
    # are optional, since it'd be a shame to add a
    # whole PersonProfile model just to add one of
    # these common fields for a single deployment.
    # feel free to add things here, but ONLY immutable
    # values. things like _height_ and _weight_ change
    # over time, so should be linked via a ForeignKey
    date_of_birth = models.DateField("Date of Birth", blank=True)
    gender        = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)


    class Meta:
        # TODO: order people by their
        # location (code?) then code
        #ordering = ["name"]
        pass

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return "<Person #%r>" % (
            self.pk or "??")


    def lookup(self, location=None, reporter=None):
        #self.objects.filter()
        pass
