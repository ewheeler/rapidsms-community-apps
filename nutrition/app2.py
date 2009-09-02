#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import date, datetime
from strings import ENGLISH as STR

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

import rapidsms
from rapidsms.message import Message
from rapidsms.connection import Connection
from rapidsms.parsers.keyworder import * 

from  models import * 
import graph
import utils

class App(rapidsms.app.App):
    msgs = {"report":""}

    # lets use the Keyworder parser!
    kw = Keyworder()

    def parse(self, message):
        self.handled = False 


    def handle(self, message):
        try:
            if hasattr(self, "kw"):
                try:
                    # attempt to match tokens in this message
                    # using the keyworder parser
                    func, captures = self.kw.match(self, message.text)
                    func(self, message, *captures)
                    # short-circuit handler calls because 
                    # we are responding to this message
                    return self.handled 
                except Exception, e:
                    # TODO only except NoneType error
                    # nothing was found, use default handler
                    self.incoming_entry(message)
                    return self.handled 
            else:
                self.debug("App does not instantiate Keyworder as 'kw'")
        except Exception, e:
	    # TODO maybe don't log here bc any message not meant
	    # for this app will log this error
	    #
            # self.error(e) 
	    pass


    def outgoing(self, message):
        pass 

    # Report 9 from outer space
    @kw("help (.+?)")
    def report(self, message, more=None):

    @kw("report (.*?) (.*?) (.*?) (.*?) (.*?) (.*?) (.*?)")
    def report(self, message, gmc, child, wt, ht, muac, oedema, diarrhea):
                infsss = INFSS(patient=patient, location=gmc,height=v[i+1],weight=v[i+2],muac=v[i+3],oedema=v[i+4],diarrea=v[i+5])
    
    @kw("cancel (.*?) (.*?)")
    def cancel(self, message, gmc, child):
        
    
    #child is now a first name 
    @kw("new (.*?) (.*?) (.*?) (.*?) (.*?)")
    def newpatient(self, message, gmc, child, sex, age contact):
        r = Reporter()
        r.save()
        alias = r.id

        p = Person(location=gmc, reporter= 
    location    = models.ForeignKey(Location)
    reporter    = models.ForeignKey(Reporter)
    lastupdated = models.DateTimeField(auto_now_add=True)
    type        = models.CharField(max_length=10,choices=P_TYPES,default="Child") #bogus
    errors      = models.IntegerField(max_lenght=5,defaul=0) # this is an HSA field
