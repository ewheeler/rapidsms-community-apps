import rapidsms
import threading
import time

from models import *
from apps.tree.models import Tree
from datetime import datetime, timedelta

class App (rapidsms.app.App):
    def start (self):
        # we have to register our functions with the tree app
        self.tree_app = self.router.get_app("tree")
        self.tree_app.register_custom_transition("validate_birth_year", self.validate_birth_year)
        self.tree_app.register_custom_transition("validate_0_to_7", self.validate_0_to_7)
        self.tree_app.register_custom_transition("validate_0_to_30", self.validate_0_to_30)
        
        # interval to check for new surveys (in seconds)
        survey_interval = 60
        # start a thread for initiating surveys
        survey_thread = threading.Thread(
                target=self.survey_initiator_loop,
                args=(survey_interval,))
        survey_thread.daemon = True
        survey_thread.start()

    def parse (self, message):
        """Parse and annotate messages in the parse phase."""
        pass

    def handle (self, message):
        """Add your main application logic in the handle phase."""
        pass

    def cleanup (self, message):
        """Perform any clean up after all handlers have run in the
           cleanup phase."""
        pass

    def outgoing (self, message):
        """Handle outgoing message notifications."""
        pass

    def stop (self):
        """Perform global app cleanup when the application is stopped."""
        pass


    def validate_0_to_7(self, msg):
        return self.validate_numeric_range(msg, 0, 7)
    
    def validate_0_to_30(self, msg):
        return self.validate_numeric_range(msg, 0, 30)
    
    def validate_numeric_range(self, msg, lower_bound, upper_bound):
        '''Validates a numeric range, parsing the message as a number
           and then checking if that number falls between the lower and
           upper bound (inclusive).'''
        value = msg.text.strip()
        if value.isdigit():
            if lower_bound <= int(value) <= upper_bound:
                return True
        return False
    
    def validate_birth_year(self, msg):
        rep = HarvardReporter.objects.get(pk=msg.reporter.pk)
        return msg.text == rep.year_of_birth
    
    def _initiate_tree_sequence(self, user):
        user_conn = user.connection()
        if user_conn:
            tree= self._get_tree(user)
            if self.tree_app:
                self.tree_app.start_tree(tree, user_conn)
            
        else:
            error = "Can't find connection %s.  Messages will not be sent" % user_conn
            self.error(error)
            return error

    def _get_tree(self, user):
        # this is very hacky
        # todo
        return Tree.objects.get(trigger="harvard 1")
        
    
    # Survey Initiator Thread --------------------
    def survey_initiator_loop(self, seconds=60):
        '''This loops and initiates surveys with registered participants
           based on some criteria (like daily)'''
        self.info("Starting survey initiator...")
        prev_time = (datetime.now() + timedelta(hours=2))
        while True:
            # wait for the time to pass when they registered to start a survey
            # and when it is, start it
            
            try: 
                # super hack... add 2 hours because of the time zone difference
                # i'm sure there is a better way to do this with real time zones
                # but i'm also sure I don't want to figure it out right now
                now_adjusted =  datetime.now() + timedelta(hours=2) 
                self.debug("Adjusted time: %s, checking for participants to notify" % str(now_adjusted))
                # ok, here's the rules for this study
                # questions are asked every 10 days.
                # if they don't respond we ask again in 1 hour.
                # if they don't respond to that we ask again in 1 day.
                # if they don't respond to that we ask again in another day.
                # if they don't respond to that we wait till the next 10-day 
                # cycle.
                # so we need to know a few things to know if we should start
                # a sequence:
                # 1.  The state 
                # 2.  The time we last asked
                
                to_initiate = StudyParticipant.objects.filter\
                    (next_question_time__gt=prev_time).filter\
                    (next_question_time__lte=now_adjusted)
                for participant in to_initiate:
                    self.debug("Initiating sequence for %s" % participant.reporter);
                    try:
                        errors = self._initiate_tree_sequence(participant.reporter) 
                        # unfortunately I'm not sure what else we can do if something
                        # goes wrong here
                        if errors:
                            self.debug("unable to initiate sequence for %s" % participant)
                            self.error(errors)
                    except Exception, e:
                        self.debug("unable to initiate sequence for %s" % participant)
                        self.error(e)
                    # also update the state and next times in our study
                    # participant list
                    self.update_participant(participant)
                    
                #update the previous time
                prev_time = now_adjusted

            except Exception, e:
                # if something goes wrong log it, but don't kill the entire loop
                self.debug("survey initiation loop failure")
                self.debug(e)
            # wait until it's time to check again
            time.sleep(seconds)

    def update_participant(self, participant):
        if participant.state == "3":
            return self.reset_participant_to_next_interval(participant)
        else:
            if participant.state == "0":
                participant.next_start_time = participant.next_start_time +\
                    timedelta(days=10)
            delta = self.get_next_time_interval(participant.state)
            participant.next_question_time = participant.next_question_time + delta 
            participant.state = str(int(participant.state) + 1)
            participant.save()
            return participant
    
    def reset_participant_to_next_interval(self, participant):
        participant.next_question_time = participant.next_start_time 
        participant.state = "0"
        participant.save()
        return participant
    
    def get_next_time_interval(self, state):
        if (state == "0"):
            return timedelta(hours=1)
        elif (state == "1"):
            return timedelta(hours=23)
        elif (state == "2"):
            return timedelta(days=1)
        elif (state == "3"):
            return timedelta(days=8)
        raise Error("%s is not a valid state!" % state)
        