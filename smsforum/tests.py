from rapidsms.tests.scripted import TestScript
from apps.reporters.models import *
import apps.smsforum.app as reporter_app
import apps.default.app as default_app
from app import App
from django.core.management.commands.dumpdata import Command
import time
import random
import os        
from datetime import datetime

class TestApp (TestScript):
    apps = (reporter_app.App, App )

    # the test_backend script does the loading of the dummy backend that allows reporters
    # to work properly in tests
    def setUp(self):
        TestScript.setUp(self)
        #should setup default village in here

    testJunk = """
           8005551210 > #djoin blargh        
    """
    
    testJoinAndBlast = """
           8005551210 > ###dcreate village
           8005551210 < village village created
           8005551210 > #djoin village
           8005551210 < first-login village
           8005551210 > msg_to_blast
           8005551210 < success! village recvd msg: msg_to_blast
           8005551210 > #name Joe
           8005551210 < Hello Joe!
        """

    testGroupBlast = """
           8005551212 > ###dcreate village2
           8005551212 < village village2 created
           8005551212 > #djoin village2
           8005551212 < first-login village2
           8005551213 > #djoin village2
           8005551213 < first-login village2
           8005551212 > msg_to_blast
           8005551213 < msg_to_blast - sent to [village2] from 8005551212
           8005551212 < success! village2 recvd msg: msg_to_blast
           8005551212 > #name Joey
           8005551212 < Hello Joey!
           8005551212 > msg_to_blast
           8005551213 < msg_to_blast - sent to [village2] from Joey
           8005551212 < success! village2 recvd msg: msg_to_blast
           8005551212 > #dleave
           8005551212 < leave-success village2
        """

    testMegaGroupBlast = """ 
           8005551215 > ###dcreate village3
           8005551215 < village village3 created
           8005551215 > #djoin village3
           8005551215 < first-login village3
           8005551216 > #djoin village3
           8005551216 < first-login village3
           8005551217 > #djoin village3
           8005551217 < first-login village3
           8005551218 > #djoin village3
           8005551218 < first-login village3
           8005551219 > #djoin village3
           8005551219 < first-login village3
           8005551215 > msg_to_blast
           8005551216 < msg_to_blast - sent to [village3] from 8005551215
           8005551217 < msg_to_blast - sent to [village3] from 8005551215
           8005551218 < msg_to_blast - sent to [village3] from 8005551215
           8005551219 < msg_to_blast - sent to [village3] from 8005551215
           8005551215 < success! village3 recvd msg: msg_to_blast
           8005551215 > #dleave
           8005551215 < leave-success village3 
        """
    
    # test lang after you have localization set up properly
    """
           8005551212 > #dlang eng
           8005551212 > lang-set
           8005551212 > ###create village2
           8005551212 < village village2 created
           8005551212 > pu#join village2
           8005551212 > #lang eng
           8005551212 > msg_to_blast
           8005551212 > #lang fre
           8005551212 > msg_to_blast
           8005551212 > #lang wol
           8005551212 > msg_to_blast
           8005551212 > #lang dyu
           8005551212 > msg_to_blast
           8005551212 > #lang pul
           8005551212 > msg_to_blast
        """
        


