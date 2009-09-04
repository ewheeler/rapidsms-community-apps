#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from datetime import date, datetime

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import F

import rapidsms
from rapidsms.message import Message
from apps.logger.models import * 
from rapidsms.connection import Connection
from rapidsms.parsers.keyworder import * 

from  models import * 
import messages

class App(rapidsms.app.App):

    # lets use the Keyworder parser!
    kw = Keyworder()

    def parse(self, message):
        self.handled = False 



    def handle(self, message):
        # log message
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

    def __log_status(self, message, status,person): 
        pass
    
    def __log_error(self, e,message, *args, **kwargs): 
        pass
   

    def __get_reporter(self,message): #THIS SHOULD BE IN REPORTER CLASS
        conn = PersistantConnection.from_message(message)
        if conn.reporter is null: 
            reporter = Reporter(alias=message.identity,last_name  = message.identity)
            reporter.save()
        conn.reporter = reporter
        conn.save()
        return conn.reporter


    def __get_person_by_identity(self,message):
        try:
            reporter = PersistantConnection.objects.filter(backend=message.connection.backend,identity=message.connection.identity).reporter
            person = Person.objects.filter(reporter=reporter,active=True) #this should be only one
            return person
        except Exception,e:
            raise Exception(EXCEPT_MSG["NO PERSON"])

    def __check_gmc(self,message,gmc,person):
        return person.location == gmc

    def __get_person(self,message,id):
        try:
            return Person.objects().get(id=id) #exists
        except:
            raise Exception(EXCEPT_MSG["NO_PERSON"])

    def __validate_data(self,*args,**kwargs):
        #use reflection
        status = []
        person, reporter, height,weight,muac,oedema,diarrea = args
        return status 

    # Report 9 from outer space
    @kw("help (.+?)")
    def report(self, message, more=None):
        pass #handle this by infss client


    @kw("report (.*?) (.*?) (.*?) (.*?) (.*?) (.*?) (.*?)")  #we dont need gmc
    def report(self, message, gmc, child, wt, ht, muac, oedema, diarrhea):

        #this should be reflection 
        person = self.__get_person_by_identity(message)
        status = self.__validate_nutrition_data(person,gmc,child,wt,ht,muac,oedema,diarrea)
         
        try:
            nut = Nutrition(patient=patient_id,reporter=person.id, height=ht, weight=wt,muac=muac,oedema=oedema,diarrea=diarrea)
            nut.save()
        except Exception,e:
            self.__log_error("report",e,message,gmc,child,wt,ht,muac,oedema,diarrea)

        
    @kw("reporter (.*?) (.*?)")
    def reporter(self, message, gmc):
        try: 
            person = self.__get_person_by_identity(message)
            if not(self._check_gmc(gmc,person)): 
                person.location = gmc
                person.save()
            else:
                self.__log_error("reporter","no change",message,gmc,child) #hard coded bad
        except:
                try:
                    reporter = self.__get_reporter(message)
                    person = Person(location=gmc,reporter=reporter,type="HSA")  #type wil change)
                    person.save()
                except Exception,e:
                    self.__log_error("reporter",e,message,gmc,child)
                
        
    
    @kw("cancel (.*?) (.*?)")
    def cancel(self, message, gmc,child):
        try: 
            person = self.__get_person_by_identity(message)
            if (self.__check_gmc(message,person)):
                n = Nutrition.objects().filter(reporter=person,patient=child).latest()[0]
                n.delete()
            else:
                self.__log_error("cancel","no person",message,gmc,child) #hard coded bad
        except Exception,e:
                self.__log_error("cancel",e,message,gmc,child) #hard coded bad
    
    @kw("exit (.*?) (.*?)")
    def exitpatient (self, message, gmc,child):
        try:
            person = Person.objects.filter(location=gmc,reporter=child) #change this to id
            person.active = False
            person.save()
        except Exception,e:
            self.__log_error("newpatient",e,message,gmc,child,gender,age,contact)

    @kw("new (.*?) (.*?) (.*?) (.*?) (.*?)")
    def newpatient(self, message, gmc, child, gender, age, contact):
        try:

            reporter = self.__get_reporter(message)
            reporter.gender = sex
            reporter.dob = Reporter.dob_from_age(float(age),"M") #is M bogus
            r.save()
            if contact: 
                conn = PersistantConnection.from_message(message)
                conn.reporter = r
                conn.save()
            person = Person(location=gmc,reporter=reporter,type="Child")  #type wil change)
            person.save()
        except:
            self.__log_error("newpatient",e,message,gmc,child,gender,age,contact)

