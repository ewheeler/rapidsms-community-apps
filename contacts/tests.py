from rapidsms.tests.scripted import TestScript
from apps.reporters.models import *
import apps.contacts.app as reporter_app
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
        
    testJoin = """
           8005551212 > ###create village
           8005551212 > #join village
           8005551213 > #join village
           8005551212 > blast
           8005551212 > blast again
           8005551212 > #leave
         """
    
 