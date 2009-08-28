#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import django


def followable_models():
    """Returns an array of every followable model in the current project. Models
       contained by apps which are present but not running are ignored. To make
       a model followable, set the "followable" attribute to True."""

    return filter(
        lambda o: getattr(o, "followable", False),
        django.db.models.loading.get_models())
