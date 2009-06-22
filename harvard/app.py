import rapidsms
import threading
import time
import sys
import random

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
        
        self.tree_app.set_session_listener("harvard 1", self.handle_session)
        self.tree_app.set_session_listener("harvard 2", self.handle_session)
        self.tree_app.set_session_listener("harvard 3", self.handle_session)
        self.tree_app.set_session_listener("harvard child 1", self.handle_session)
        self.tree_app.set_session_listener("harvard child 2", self.handle_session)
        self.tree_app.set_session_listener("harvard child 3", self.handle_session)
        
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
        return msg.text == rep.pin
    
    def _initiate_tree_sequence(self, participant):
        user = participant.reporter
        # have to intelligently choose whether to continue
        # with the same tree or initiate a new one based on the
        # state the participant is in.
        user_conn = user.connection()
        if user_conn:
            if participant.state == "0":
                # this is the normal case.  just get a new tree
                # and fire up a session
                tree = self._get_tree(user)
                self.debug("Starting session for %s.  Chose tree: %s" % (user, tree))
            else:
                # this means we are re-sending a previous attempt
                if not participant.active_report:
                    # this shouldn't be possible.  what should we do?
                    raise Exception("Participant tried to restart a non-existant session!")
                tree = participant.active_report.session.tree
                self.debug("restarting session for %s.  Chose tree: %s" % (user, tree))
            if self.tree_app:
                self.tree_app.start_tree(tree, user_conn)
        else:
            error = "Can't find connection %s.  Messages will not be sent" % user_conn
            self.error(error)
            return error

    def _get_tree(self, user):
        # the tree should be semi-randomly 
        # selected among the three valid options 
        # which are dependent on adult/child status
        # BUT if any of the three has been answered less
        # than the others then only select from the trees
        # with fewer answers
        if (user.is_child):
            trees = {Tree.objects.get(trigger="harvard child 1") : 0,
                     Tree.objects.get(trigger="harvard child 2") : 0,
                     Tree.objects.get(trigger="harvard child 3") : 0}
        else:
            trees = {Tree.objects.get(trigger="harvard 1") : 0,
                     Tree.objects.get(trigger="harvard 2") : 0,
                     Tree.objects.get(trigger="harvard 3") : 0}
        
        prev_reports = HarvardReport.objects.filter(reporter=user)
        for report in prev_reports:
            if report.session.tree in trees:
                trees[report.session.tree] += 1

        min_count = sys.maxint
        to_use = []
        for tree, val in trees.items():
            if val < min_count:
                # new minimum, clear the list of options to just this
                min_count = val
                to_use = [tree]
            elif val == min_count:
                # it's the same value, add it to the list of options
                to_use.append(tree)
            else:
                # it's too big, ignore it
                pass
        
        return random.choice(to_use)
        
    def _get_clean_answer(self, answer, value):
        # this is just hard coded. *sigh*
        if answer.name == "don't know":
            return None
        else:
            return int(value)
    
    
    def handle_session(self, session, is_ending):
        self.debug("harvard session: %s" % session)
            
        # get the reporter object
        reporter = session.connection.reporter
        harvard_reporter = HarvardReporter.objects.get(pk=reporter.pk)
        participant = None
        try:
            participant = StudyParticipant.objects.get(reporter=harvard_reporter)
        except StudyParticipant.DoesNotExist:
            # how did they get here?  
            pass
        if not is_ending:
            # this could either be a re-initiation of the same survey
            # or a new one altogether.  Use the state to determine this
            if participant:
                if participant.state == "0":
                    # new session
                    new_session = True
                else:
                    # repeater
                    # just update the count of the number of retries
                    new_session = False
                    report = participant.active_report
                    if not report:
                        # this shouldn't be possible.  what should we do?
                        raise Exception("Participant tried to restart a non-existant session!")
                    report.num_tries = report.num_tries + 1
                    report.status = "A"
                    report.session = session
                    report.save()  
            else:
                # if they're not a participant we don't have much to go on
                new_session = True
            if new_session:
                report = HarvardReport.objects.create(reporter=harvard_reporter, 
                                                      started=session.start_date, 
                                                      session=session,
                                                      num_tries=1, 
                                                      status="A")
                # link the active report
                if participant:
                    participant.active_report = report
                    participant.save()
        else:
            # if we have a report
            # update the data and save
            try:
                # there are three things that could be happening here
                # this could be a valid completion
                # it could be a cancellation because we are restarting
                # or it could be a full cancellation
                # the last two can be treated the same
                report = HarvardReport.objects.get(session=session)
                if session.canceled:
                    # it was canceled.  temporarily set the status
                    # keeping in mind that if it gets completed
                    # at a later point it will be overwritten
                    report.status = "C"
                else: 
                    # it was finished. get the answer out and 
                    # set the status to finished
                    for entry in session.entry_set.all():
                        answer = entry.transition.answer
                        if answer.name != "birth year validation":
                            # there's only one other answer 
                            # in all the studies, and it's the 
                            # one we want to save
                            clean_answer = self._get_clean_answer(answer, entry.text)
                            report.answer = clean_answer 
                    report.completed = datetime.now()
                    report.status = "F"
                    # we also should update the participant to the next interval
                    if participant:
                        self.reset_participant_to_next_interval(participant)
                        # the report is no longer active
                        participant.active_report = None
                        participant.save()
                report.save()
            except HarvardReport.DoesNotExist:
                # oops, not sure how this could happen, but we don't
                # want to puke
                self.error("No report found for session %s" % session)



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
                # questions are asked every 7 days.
                # if they don't respond we ask again in 1 hour.
                # if they don't respond to that we ask again in 1 day.
                # if they don't respond to that we ask again in another day.
                # if they don't respond to that we wait till the next 7-day 
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
                        errors = self._initiate_tree_sequence(participant) 
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
        # in case the participant was updated between when we loaded
        # him and when this method was called 
        participant = StudyParticipant.objects.get(id=participant.id)
        if participant.state == "3":
            return self.reset_participant_to_next_interval(participant)
        else:
            if participant.state == "0":
                participant.next_start_time = participant.next_start_time +\
                    timedelta(days=7)
            delta = self.get_next_time_interval(participant.state)
            participant.next_question_time = participant.next_question_time + delta 
            participant.state = str(int(participant.state) + 1)
            participant.save()
            return participant
    
    def reset_participant_to_next_interval(self, participant):
        # in case the participant was updated between when we loaded
        # him and when this method was called 
        participant = StudyParticipant.objects.get(id=participant.id)
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
            return timedelta(days=5)
        raise Error("%s is not a valid state!" % state)
    
    def get_next_time_interval_testing(self, state):
        '''Speeds up the survey intervals (a lot) for quick
           testing of the polling logic.'''
        if (state == "0"):
            return timedelta(seconds=30)
        elif (state == "1"):
            return timedelta(seconds=30)
        elif (state == "2"):
            return timedelta(seconds=30)
        elif (state == "3"):
            return timedelta(seconds=30)
        raise Error("%s is not a valid state!" % state)
        