#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

import re
from datetime import datetime, timedelta
from datetime import time as dtt

from rapidsms.message import StatusCodes

from models import *
from strings import strings

from apps.reporters.models import Reporter
from apps.form.formslogic import FormsLogic
from apps.i18n.utils import get_translation as _
from apps.i18n.utils import get_language_code

class IaviFormsLogic(FormsLogic):
    ''' This class will hold the IAVI-specific forms logic. '''
    
    def validate(self, *args, **kwargs):
        message = args[0]
        form_entry = args[1]
        
        data = form_entry.to_dict()
        
        if form_entry.form.code.abbreviation == "register": 
            language = data["language"]
            site = data["location"]
            id = data["study_id"]
            # time is optional
            study_time = data["time"]
            if not study_time:
                study_time = "1600" 

            # validate the format of the id, existence of location
            if not re.match(r"^\d{3}$", id):
                return [(_(strings["id_format"], get_language_code(message.persistant_connection)) % {"alias" : id})]
            try:
                location = Location.objects.get(code=site)
            except Location.DoesNotExist:
                return[(_(strings["unknown_location"], get_language_code(message.persistant_connection)) % {"alias" : id, "location" : site})]
                
            # TODO: validate the language
            
            # validate and get the time object
            if re.match(r"^\d{4}$", study_time):
                hour = int(study_time[0:2])
                minute = int(study_time[2:4])
                if hour < 0 or hour >= 24 or minute < 0 or minute >= 60:
                    return [(_(strings["time_format"], get_language_code(message.persistant_connection)) % {"alias" : id, "time" : study_time})]
                real_time = dtt(hour, minute)
            else:
                return [(_(strings["time_format"], get_language_code(message.persistant_connection)) % {"alias" : id, "time" : study_time})]
                
            # user ids are unique per-location so use location-id
            # as the alias
            alias = IaviReporter.get_alias(location.code, id)
            
            # make sure this isn't a duplicate alias
            if len(IaviReporter.objects.filter(alias=alias)) > 0:
                return [(_(strings["already_registered"], language) % {"alias": id, "location":location.code})]
                return True
            
            data["alias"] = alias
            data["location"] = location
            data["time"] = real_time
            # all fields were present and correct, so copy them into the
            # form_entry, for "actions" to pick up again without re-fetching
            form_entry.reg_data = data
            
            return []
            
        elif form_entry.form.code.abbreviation == "test":
            print "test!"
            print data
            site = data["location"]
            id = data["study_id"]
            alias = IaviReporter.get_alias(site, id)
            try: 
                # make sure the user in question exists.  If not,
                # respond with an error
                user = IaviReporter.objects.get(alias=alias)
                
                # set some data in the form_entry so we have easy
                # access to it from within actions  
                data["reporter"] = user
                data["alias"] = alias
                form_entry.test_data = data
            except IaviReporter.DoesNotExist:
                return [(_(strings["unknown_user"], language) % {"alias":id})]
            
            
    def actions(self, *args, **kwargs):
        message = args[0]
        form_entry = args[1]

        # we'll be using the language in all our responses so
        # keep it handy
        language = get_language_code(message.persistant_connection)
        
        if form_entry.form.code.abbreviation == "register": 
            # todo: registration
            alias = form_entry.reg_data["alias"]
            language = form_entry.reg_data["language"]
            location = form_entry.reg_data["location"]
            real_time = form_entry.reg_data["time"]
            study_id =  form_entry.reg_data["study_id"]
            
            # create the reporter object for this person 
            reporter = IaviReporter(alias=alias, language=language, location=location, registered=message.date)
            reporter.save()
            
            # create the study participant for this too.  Assume they're starting
            # tomorrow and don't set a stop date.  
            start_date = (datetime.today() + timedelta(days=1)).date()
            participant = StudyParticipant.objects.create(reporter=reporter, 
                                                          start_date = start_date,
                                                          notification_time = real_time)
            
            # also attach the reporter to the connection 
            message.persistant_connection.reporter=reporter
            message.persistant_connection.save()
            
            message.respond(_(strings["registration_complete"], language) % {"alias": study_id })
            
            # also send the PIN request and add this user to the 
            # pending pins
            self.app.pending_pins[reporter.pk] = None
            message.respond(_(strings["pin_request"], language))

        elif form_entry.form.code.abbreviation == "test":
            
            # initiate the tree sequence for the user we set 
            # during validation
            user = form_entry.test_data["reporter"]
            errors = self.app._initiate_tree_sequence(user, message.persistant_connection)
            if errors:
                message.respond(errors)
            else:
                message.respond(_(strings["test_initiated"], language) % {"alias" : form_entry.test_data["study_id"]})