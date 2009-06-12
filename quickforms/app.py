#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

import rapidsms
from rapidsms.message import StatusCodes
from models import *
from actions import KeywordActions, FormActions

class App (rapidsms.app.App):

    def start (self):
        self.TOKEN_MAP = {
                "str":  "([a-z]+)",
                "float":  "(\d*\.?\d*)",
                "bool": "(yes|y|yeah|true|t|no|n|nope|false|f)"}

    def find_keywords_in(self, msg_list):
        keywords = Keyword.objects.all()
        matches = []
        def lookup(piece):
            return keywords.filter(word__iexact=piece).values_list('word', flat=True)
        for piece in msg_list:
            match = lookup(piece)
            if match.count() == 1:
                if match[0] not in matches:
                    # add keywords to matches once
                    matches.append(match[0])
                    # remove from list of pieces
                    msg_list.remove(piece)
        return (matches, msg_list) 

    def match_form_fields(self, keyword, pieces):
        # get this keyword's form
        form = keyword.form
        # fetch its fields
        fields = form.field_set.all()
        errors = []
        info = []
        # create and save a FormEntry
        # TODO also save Reporter
        formentry = FormEntry(form=form)
        formentry.save()
        for f, p in zip(fields, pieces):
            if not p:
                p = ""
            # try to match each piece based on the field's type
            result = re.match(self.TOKEN_MAP[f.data_type], p)

            if result is not None:
                data = result.group(0)
                # booleans are a special case, because we want to
                # save a consistent representation in the db rather
                # than whatever the reporter submitted -- so we can analyze
                if f.data_type == "bool":
                    if data.startswith(('y','t')):
                        data = "True"
                    if data.startswith(('n', 'f')):
                        data = "False"
                # create and save FieldEntry
                fieldentry = FieldEntry(form_entry=formentry, field=f, data=data)
                fieldentry.save()
                # add to list of info used in confirmation message
                info.append("%s=%s" % (f.title, data or "??"))
            else:
                # if we cant match (maybe there was a string where we expected
                # a number), prepare a descriptive error message 
                errors.append("Could not parse '%s' into '%s' for %s" % (p, f.data_type, f.title))
        if fields.count() != len(pieces):
            # if we are lacking data, prepare a descriptive error message
            errors.append("%s form has %d data fields. You submitted %d pieces of data" % (form.title, fields.count(), len(pieces)))
        # prepare confirmation message
        confirmation = ("Received form for %s: %s.\nIf this is not correct, reply with CANCEL" % \
            (form.description, ", ".join(info)))                        
        return (formentry, confirmation, errors)

    def handle(self, message):
        msg = message.text

        # replace multiple spaces with a single space
        # (consider running the stringcleaning app,
        # which removes commas, cleans numbers, etc)
        whitespace = re.compile("(\s+)")
        msg = re.sub(whitespace, " ", msg)

        # split message by spaces
        msg_pieces = msg.split(" ")
        # separate keywords from the other pieces
        keywords, remaining_pieces = self.find_keywords_in(msg_pieces)

        for kw in keywords:
            # retrieve Keyword object
            keyword = Keyword.objects.get(word__iexact=kw)
            kw_form = keyword.form

            if kw_form:
                # attempt to parse form fields if this keyword has a form
                formentry, confirmation, errors = self.match_form_fields(keyword, remaining_pieces)
                # respond with confirmation
                message.respond(confirmation)
                if len(errors) > 0:
                    # respond with errors, if any
                    message.respond(", ".join(errors))

                if hasattr(FormActions, keyword.word):
                    # execute any form actions defined for this keyword
                    getattr(FormActions, keyword.word)(formentry, errors)

            # gather actions for this keyword
            kw_actions = Action.objects.filter(keyword=keyword)
            for action in kw_actions:
                # check for keyword actions in actions.py
                if hasattr(KeywordActions, action.__unicode__()):
                    if action.type == "silent":
                            # call any function actions
                            getattr(KeywordActions, action.__unicode__())()

                    if action.type == "responding":
                            # call any responding actions and respond with whatever it returns
                            message.respond(getattr(KeywordActions, action.__unicode__())())

