#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


from django import template
register = template.Library()


import datetime
from django.utils.timesince import timesince
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape
from django.template.defaultfilters import date as filter_date, time as filter_time

@register.filter()
def human_readable_action(action):
    """Given a MessageLog Action, returns a human-readable interpretation of events"""
    if action == 'C':
        return "Join"
    elif action == 'D':
        return "Leave"
    return "Unknown"

