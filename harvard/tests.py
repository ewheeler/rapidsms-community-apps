from rapidsms.tests.scripted import TestScript
from app import App
import apps.reporters.app as reporters_app
import apps.tree.app as tree_app
from apps.reporters.models import PersistantBackend, PersistantConnection
from models import *
from datetime import datetime, timedelta

class TestApp (TestScript): 
    apps = (reporters_app.App, App, tree_app.App )
    # we need the iavi trees for the languages.
    # it would be better to split these out
    fixtures = ["harvard_trees", "iavi_trees"]
    
    def testHarvard(self):
        self._register(phone="harvard_1", alias="1")
        script = """
            # base case
            harvard_1 > harvard 1
            harvard_1 < Hello. Send me the year of your birth.
            harvard_1 > 1234
            harvard_1 < How many doses of your medicine did you miss in the past 7 days? If you do not know, type "n".
            harvard_1 > 2
            harvard_1 < Thank you for your response. Good-bye.
        """
        self.runScript(script)
        self._register(phone="harvard_2", alias="2")
        script = """
            # base case
            harvard_2 > harvard 2
            harvard_2 < Hello. Send me the year of your birth.
            harvard_2 > 1234
            harvard_2 < How many doses of your medicine did you miss in the past 30 days? If you do not know, type "n".
            harvard_2 > 2
            harvard_2 < Thank you for your response. Good-bye.
        """
        self.runScript(script)
        self._register(phone="harvard_3", alias="3")
        script = """
            # base case
            harvard_3 > harvard 3
            harvard_3 < Hello. Send me the year of your birth.
            harvard_3 > 1234
            harvard_3 < How many doses of medicine did you miss since the last time you picked up your medicine from the pharmacy? If you do not know, type "n".
            harvard_3 > 2
            harvard_3 < Thank you for your response. Good-bye.
        """
        self.runScript(script)
        
    def testHarvardChild(self):
        self._register(phone="havard_child_1", alias="1", is_child=True)
        script = """
            # base case
            havard_child_1 > harvard child 1
            havard_child_1 < Hello. Send me the year of your birth.
            havard_child_1 > 1234
            havard_child_1 < How many doses of medicine did your child miss in the past 7 days? If you do not know, type "n".
            havard_child_1 > 2
            havard_child_1 < Thank you for your response. Good-bye.
        """
        self.runScript(script)
        self._register(phone="havard_child_2", alias="2", is_child=True)
        script = """
            # base case
            havard_child_2 > harvard child 2
            havard_child_2 < Hello. Send me the year of your birth.
            havard_child_2 > 1234
            havard_child_2 < How many doses of medicine did your child miss in the past 30 days? If you do not know, type "n".
            havard_child_2 > 2
            havard_child_2 < Thank you for your response. Good-bye.
        """
        self.runScript(script)
        self._register(phone="havard_child_3", alias="3", is_child=True)
        script = """
            # base case
            havard_child_3 > harvard child 3
            havard_child_3 < Hello. Send me the year of your birth.
            havard_child_3 > 1234
            havard_child_3 < How many doses of medicine did your child miss since the last time you picked up his or her medicine from the pharmacy? If you do not know, type "n".
            havard_child_3 > 2
            havard_child_3 < Thank you for your response. Good-bye.
        """
        self.runScript(script)
        
    def testHarvardLocalization(self):
        # create a user with lugandan localizaiton
        self._register(phone="harvard_lg", language="lg")
        script = """
            # base case
            harvard_lg > harvard 1
            harvard_lg < Agandi, nyoherereza omwaka oguwazarirwemu.
            harvard_lg > 1234
            harvard_lg < Nemirundi engahi omubiiro mushanju eyobuziire kumiira omubazi gwawe? Ku orabe otarikugyimanya, handiika "n".
            harvard_lg > 2
            harvard_lg < Webaare kungarukamu. Ogume nobusingye.
        """
        self.runScript(script)
        script = """
            # base case
            harvard_lg > harvard 2
            harvard_lg < Agandi, nyoherereza omwaka oguwazarirwemu.
            harvard_lg > 1234
            harvard_lg < Nemirundi engahi omubiiro makumi ashatu eyobuziire kumiira omubazi gwawe? Ku orabe otarikugyimanya, handiika "n".
            harvard_lg > 2
            harvard_lg < Webaare kungarukamu. Ogume nobusingye.
        """
        self.runScript(script)
        script = """
            # base case
            harvard_lg > harvard 3
            harvard_lg < Agandi, nyoherereza omwaka oguwazarirwemu.
            harvard_lg > 1234
            harvard_lg < Nemirundi engahi eyobuziire kumiira omubazi gwawe kuruga obwohererukiire kwiiha emibazi yaawe  omwirwariro rya Mbarara? Ku orabe otarikugyimanya, handiika "n".
            harvard_lg > 2
            harvard_lg < Webaare kungarukamu. Ogume nobusingye.
        """
        self.runScript(script)
        
    def testHarvardChildLocalization(self):
        # create a user with lugandan localizaiton
        self._register(phone="harvard_child_lg", language="lg", is_child=True)
        script = """
            # base case
            harvard_child_lg > harvard child 1
            harvard_child_lg < Agandi, nyoherereza omwaka oguwazarirwemu.
            harvard_child_lg > 1234
            harvard_child_lg < Nemirundi engahi omubiiro mushanju eyo mwaana wawe abuziire kumiira omubazi gwe? Ku orabe otarikugyimanya, handiika "n".
            harvard_child_lg > 2
            harvard_child_lg < Webaare kungarukamu. Ogume nobusingye.
        """
        self.runScript(script)
        script = """
            # base case
            harvard_child_lg > harvard child 2
            harvard_child_lg < Agandi, nyoherereza omwaka oguwazarirwemu.
            harvard_child_lg > 1234
            harvard_child_lg < Nemirundi engahi omubiiro maku ashatu eyo mwaana wawe abuziire kumiira omubazi gwe? Ku orabe otarikugyimanya, handiika "n".
            harvard_child_lg > 2
            harvard_child_lg < Webaare kungarukamu. Ogume nobusingye.
        """
        self.runScript(script)
        script = """
            # base case
            harvard_child_lg > harvard child 3
            harvard_child_lg < Agandi, nyoherereza omwaka oguwazarirwemu.
            harvard_child_lg > 1234
            harvard_child_lg < Nemirundi engahi eyo mwaana waawe abuzire kumira omubazi gwe kuruga obwohererukire kwiha omubazi gwe omwirwariro Mbarara? Waba otarikugyimanya handiika "n". 
            harvard_child_lg > 2
            harvard_child_lg < Webaare kungarukamu. Ogume nobusingye.
        """
        self.runScript(script)
        
    def test_participation_logic(self):
        rep = self._register()
        now = datetime.now()
        participant = StudyParticipant.objects.create(
                                reporter=rep, start_date = now.date(),
                                notification_time=now.time(), state="0",
                                next_question_time=now, next_start_time=now)
        
        app = App("")
        participant = app.update_participant(participant)
        self.assertEqual("1", participant.state)
        date = now + timedelta(hours=1)
        next_date = now + timedelta(days=10)
        self.assertEqual(date, participant.next_question_time)
        self.assertEqual(next_date, participant.next_start_time)
        
        participant = app.update_participant(participant)
        self.assertEqual("2", participant.state)
        date = now + timedelta(days=1)
        self.assertEqual(date, participant.next_question_time)
        self.assertEqual(next_date, participant.next_start_time)
        
        participant = app.update_participant(participant)
        self.assertEqual("3", participant.state)
        date = now + timedelta(days=2)
        self.assertEqual(date, participant.next_question_time)
        self.assertEqual(next_date, participant.next_start_time)
        
        participant = app.update_participant(participant)
        self.assertEqual("0", participant.state)
        self.assertEqual(next_date, participant.next_question_time)
        self.assertEqual(next_date, participant.next_start_time)
        
        
        
        
    def _register(self, phone="55555", alias="001", yob="1234", is_child=False,language="En"):
        """Register a user"""
        # create the reporter object for this person 
        reporter =  HarvardReporter(alias=alias, language=language, year_of_birth=yob)
        reporter.save()
        # running this script ensures the connection gets created by the reporters app
        self.runScript("%s > hello world" % phone)
        connection = PersistantConnection.objects.get(identity=phone)
        connection.reporter = reporter
        connection.save()
        return reporter
    