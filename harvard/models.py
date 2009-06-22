from django.db import models

from apps.reporters.models import Reporter
from apps.tree.models import Session

class HarvardReporter(Reporter):
    """This model represents a reporter in the Harvard Study.  
       They are an extension of the basic reporters, 
       but also have years of birth"""  
       
    pin = models.CharField(max_length=4, null=True, blank=True)
    is_child = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.alias
    
    class Meta:
        # the permission required for this tab to display in the UI
        permissions = (
            ("can_view", "Can view harvard data"),
        )


        
class StudyParticipant(models.Model):
    """ This represents a participant in the Harvard study. """
    reporter = models.ForeignKey(HarvardReporter)
    start_date = models.DateField()
    
    # if the end_date is blank the study will go indefinitely
    end_date = models.DateField(null=True, blank=True)
    notification_time = models.TimeField()
    
    # the different states that this can be in
    SESSION_STATES = (
        ('0', 'Normal, waiting for the next 10-day cycle.'),
        ('1', 'Asked once, waiting for 1 hour.'),
        ('2', 'Asked twice, waiting for 1 day.'),
        ('3', 'Asked three times, waiting for 1 day.'),
    )
    state = models.CharField(max_length="1", choices=SESSION_STATES)
    # this stores the time of the next question, based on 
    # the state
    next_question_time = models.DateTimeField(null=True, blank=True)
    # this stores the time of the next cycle, and should
    # be updated in 10-day increments
    next_start_time = models.DateTimeField(null=True, blank=True)
    
    # stores the current active session with the tree app
    active_report = models.ForeignKey("HarvardReport", null=True, blank=True)
    
    def __unicode__(self):
        return "%s: %s - %s" % (self.reporter, self.start_date, self.end_date)

class HarvardReport(models.Model):
    STATUS_TYPES = (
        ('C', 'Canceled'),
        ('A', 'Active'),
        ('F', 'Finished'),
    )

    reporter = models.ForeignKey(HarvardReporter)
    session = models.ForeignKey(Session)
    started = models.DateTimeField()
    completed = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=1, choices=STATUS_TYPES)
    
    answer = models.IntegerField(null=True, blank=True)
    # the number of times we had to initiate this survey before 
    # it was successful (if it was sucessful)
    num_tries = models.IntegerField()
    
    @property
    def is_child(self):
        return self.reporter.is_child
    
    @classmethod
    def pending_sessions(klass):
        return klass.objects.filter(completed=None)
    
    def __unicode__(self):
        return "%s: %s (%s)" % (self.reporter, self.started, self.get_status_display())
    
    