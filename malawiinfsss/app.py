#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4


import re
import rapidsms
import datetime
from models import *


#CRAPPY WITH TOO MUCH HARD CODING - BUT WANT SOMETHING TO GET STARTED WITH

class App(rapidsms.app.App):
    #Upgrade this to keyword parser
    #NEW = re.compiler(r"^(new|add|exit|help)\ (.*?)\ ?(.*?)\ ?(.*?)\ ?(.*?)\ ?(.*?)\ ?
    RESP = ["new reading: n GMCid ChildID Weight(0.0) Height(0.0) MUAC(0.00) Oedema(Y/N) Diarrhoea(Y/N)",\
            "add child: a Sex(M/F) AgeInMonths GMCid Weight(0.0) Height(0.0) MUAC(0.00) Oedema(Y/N) Diarrhoea(Y/N)",\
            "h ([N]ew reading,[A]dd child)- enter h n or h a",\
            "Please resend your message, type h for more help",\
            "Unable to find GMCId - please fix the Id and resend the message. type: h n -for more help"\
            "Please add a child: a Sex(M/F) AgeInMonths"\
            "Thank you for the excellent data reading."\
            "Thank you for the excellent data reading - The Child Id is %s"]




    def __find_patient(self, text):
        try:
            return Patient.objects.get(id=text)

        except Patient.DoesNotExist:
            return None

    #can i inherit this?
    def __find_gmc(self, text):
        try:
            #we only want gmc sites
            return Location.objects.get(id=text,type=4)

        except Location.DoesNotExist:
            return None

    def parse(self, msg):
      
        #Use Keyword parser - I dont need regex for this test

        #sort of crap bu lets get something out teh door
        #not so into index paradigm
        #creates will not work
        param = ()

        respindex = 3 
        if msg is not None: 

            v = msg.split(" ") #tokenize because I am bogus - will fix w/ field feedback
            if ("h" in v[0] ):
                respindex = int("a" in msg)
                #respindex = "h" in v[0] * int("a" in msg) too insane perhaps
            else: 
                # is first token a number or letter  set i
                i = 0
                        
                if ("n" in v[0]) or (len(v) == 7): 
                    patient = self.__find_patient_id(v[i+1]) 
                elif ("a" in v[0]):
                        patient =   Patient(gender=v[i],system=1, dob=datetime.datetime.now()+datetime.timedelta(v[i+1]*30)
                        patient.save()
                gmc = self.__find_gmc(v[i])
                if patient is None : respindex = 5
                if gmc is None : respindex = 4
                infsss = INFSS(patient=patient, location=gmc,height=v[i+1],weight=v[i+2],muac=v[i+3],oedema=v[i+4],diarrea=v[i+5])
                infsss.save()
                param =  (patient.id)
             
            msg.respond = RESP[respindex] % param

