#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import date, datetime

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

import rapidsms
from rapidsms.message import Message
from rapidsms.connection import Connection
from rapidsms.parsers.keyworder import * 

from  models import * 

class App(rapidsms.app.App):
    msgs = {"help":""}

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

