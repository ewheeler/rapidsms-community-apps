#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from utils import followable_models
from django.db import models
from apps.reporters.models import Reporter, PersistantConnection


for model in followable_models():
    m_name = "Following%s" % model.__name__
    
    # believe it or not, this is how django generates the field names for
    # many-to-one (reverse foreign key) relationships. so i'm doing the same.
    # see: django.db.models.fields.related.RelatedField.contribute_to_class
    f_name = "following_%s" % model.__name__.lower()
    r_name = "%s_set" % f_name

    vars()[m_name] = type(m_name, (models.Model,), {
        f_name: models.ForeignKey(model, related_name="followers"),

        # allow reporters OR connections to follow other objects. this doesn't
        # make much sense, but is allowed for the sake of completeness. it can
        # always be disallowed in app.py
        "reporter": models.ForeignKey(Reporter, null=True, related_name=r_name),
        "connection": models.ForeignKey(PersistantConnection, null=True, related_name=r_name),

        # replace the verbose name, to shorten the
        # names in the admin. this will probably
        # be useful for other things, too...
        "Meta": type("Meta", (object,), {
            "verbose_name": model._meta.verbose_name
        }),

        # for debugging in the console
        "__repr__": lambda self:\
            "<%s: %r by %r>" % (
                type(self).__name__,
                getattr(self, type(self)._meta._fields()[1].name),
                self.reporter or self.connection),

        # for viewing in the django admin
        "__unicode__": lambda self:\
            u"%s following %s" % (
                self.reporter or self.connection,
                getattr(self, type(self)._meta._fields()[1].name)),

        # these are necessary to let django know which app this dynamic
        # class lives within. i don't quite understand it, but i suspect
        # it's because django expects models to be declared statically.
        # (see django.db.models.base.ModelBase.__new__ for context)
        "__module__": __name__
    })
