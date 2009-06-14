from rapidsms.tests.scripted import TestScript
from rapidsms import message,connection,person
from rapidsms.backends import test
from app import App
import apps.nodegraph.app as nodegraph_app
from models import *
import apps.contacts.models as contacts_models
from apps.contacts.models import *
from apps.smsforum.models import Village,Community
import time

# helpers
def _user(name, *grps):
    u=Contact(debug_id=name)
    u.save()
    for grp in grps:
        u.add_to_group(grp)

    return u

def _group(name, *children):
    g=NodeSet(debug_id=name)
    g.save()
    g._add_subnodes(*children)
    return g

class TestApp (TestScript):
    apps = (App, nodegraph_app.App)
 
#    fixtures = ['test_backend', 'test_tree']
    
#     testPin = """
#           8005551211 > pin
#           8005551211 < Please enter your 4-digit PIN
#           8005551211 > 1234
#           8005551211 < Thanks for entering.
#         """
 
    # some globals for all tests
    m_nodes=None
    w_nodes=None
    m_group=None
    w_group=None
    people_group=None
    
    m_names = ['matt','larry','jim','joe','mohammed']
    w_names = ['jen','julie','mary','fatou','sue']
        

    def setUp(self):
        TestScript.setUp(self)
        
        # make some nodes and graphs
        # imagine this is users and groups for clarity
        self.m_nodes = [_user(n) for n in self.m_names]
        self.w_nodes = [_user(n) for n in self.w_names]
        
        self.m_group = _group('men',*self.m_nodes)
        self.w_group = _group('women',*self.w_nodes)
        self.people_group = _group('people', self.m_group, self.w_group)
        
        self.backend=test.Backend(None)

    def testPrint(self):
        print "\nPrint Test:"
        print self.people_group

    def testChannelConnectionFromMessage(self):
        print "\nPrint Channel Connection Test:"
        con1=connection.Connection(self.backend,'4153773715')
        msg=message.Message(con1, 'test message')
        print contacts_models.ChannelConnectionFromMessage(msg)
        msg = message.Message(con1, 'Another Message')
        print contacts_models.ChannelConnectionFromMessage(msg)
        pass
        






        
        
