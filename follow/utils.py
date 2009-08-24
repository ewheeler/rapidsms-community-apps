#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import django


def followable_models():
    """Returns an array containing every model that implements the
       __search__ API. Does not search the django.* namespace."""

    return [
        model
        for model in django.db.models.loading.get_models()
        if model.__module__[0:7] != "django." and
           hasattr(model, "__search__")]
