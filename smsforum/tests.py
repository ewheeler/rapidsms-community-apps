#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4 encoding=utf-8

from rapidsms.tests.scripted import TestScript
import apps.smsforum.app as smsforum_app
import apps.smsforum.app as smsforum_app
import apps.logger.app as logger_app
import apps.contacts.app as contacts_app
from app import App
from django.core.management.commands.dumpdata import Command
import time
import random
import os
from datetime import datetime
 
class TestApp (TestScript):
    apps = (smsforum_app.App, contacts_app.App, logger_app.App, App )

    def setUp(self):
        TestScript.setUp(self)
        #should setup default village in here
    testAllCommandsFrench = """
            8005551220 > .creer village4
            8005551220 < Community 'village4' was created
            8005551220 > .entrer village4
            8005551220 < Thank you for joining the village4 community - welcome!
            8005551220 > message to blast
            8005551220 < Your message was sent to these communities: village4
            8005551220 > .nom foo
            8005551220 < Hello foo!
            8005551220 > .quitter village4
            8005551220 < You have left these communities: village4
            8005551220 > .language fra
            8005551220 < La langue que vous avez sélectionnée est 'Français'
            8005551220 > .aide
            8005551220 < Available Commands: #join COMMUNITY - #leave - #name NAME - #lang LANG
            """
         


testJoinAndBlast = """
    8005551210 > .create village
    8005551210 < Community 'village' was created
    8005551210 > .join village
    8005551210 < Thank you for joining the village community - welcome!
    8005551210 > message to blast
    8005551210 < Your message was sent to these communities: village
    """

testGroupBlast = """
    8005551212 > .create village2
    8005551212 < Community 'village2' was created
    8005551212 > .join village2
    8005551212 < Thank you for joining the village2 community - welcome!
    8005551213 > .join village2
    8005551213 < Thank you for joining the village2 community - welcome!
    8005551212 > msg_to_blast
    8005551212 < Your message was sent to these communities: village2
    8005551213 < msg_to_blast - 8005551212
    8005551212 > .leave
    8005551212 < You have left these communities: village2
    """

testMegaGroupBlast = """
    8005551215 > .create village3
    8005551215 < Community 'village3' was created
    8005551215 > .join village3
    8005551215 < Thank you for joining the village3 community - welcome!
    8005551216 > .join village3
    8005551216 < Thank you for joining the village3 community - welcome!
    8005551217 > .join village3
    8005551217 < Thank you for joining the village3 community - welcome!
    8005551218 > .join village3
    8005551218 < Thank you for joining the village3 community - welcome!
    8005551219 > .join village3
    8005551219 < Thank you for joining the village3 community - welcome!
    8005551215 > msg_to_blast
    8005551215 < Your message was sent to these communities: village3
    8005551216 < msg_to_blast - 8005551215
    8005551217 < msg_to_blast - 8005551215
    8005551218 < msg_to_blast - 8005551215
    8005551219 < msg_to_blast - 8005551215
    8005551215 > .leave
    8005551215 < You have left these communities: village3
    """
    
testLang = """
    8005551212 > .lang eng
    8005551212 < You language has been set to: English
    8005551212 > .lang fra
    8005551212 < La langue que vous avez sélectionnée est 'Français'
    8005551212 > .lang wol
    8005551212 < Làkk wi nga tànn moo kàllaama Wolof
    8005551212 > .lang joo
    8005551212 < kasankenak kanu fajulumi ku 'Joola'
    8005551212 > .lang pul
    8005551212 < Åemngal ngal cuøi- daa ko Pulaar.
    """

testAllCommandsEnglish = """
    8005551220 > .create village4
    8005551220 < Community 'village4' was created
    8005551220 > .join village4
    8005551220 < Thank you for joining the village4 community - welcome!
    8005551220 > message to blast
    8005551220 < Your message was sent to these communities: village4
    8005551220 > .name foo
    8005551220 < Hello foo!
    8005551220 > .member
    8005551220 < You are a member of these communities: village4
    8005551220 > .citizens village4
    8005551220 < village4: 8005551220
    8005551220 > .leave village4
    8005551220 < You have left these communities: village4
    8005551220 > .remove village4
    8005551220 < The community 'village4' was removed.
    8005551220 > .language eng
    8005551220 < You language has been set to: English
    8005551220 > .help
    8005551220 < Available Commands: #join COMMUNITY - #leave - #name NAME - #lang LANG
    """

