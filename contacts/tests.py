from rapidsms.tests.scripted import TestScript
from rapidsms.backends import test
from app import App
import apps.contacts.app as contacts_app
#from models import *
import apps.contacts.models as contacts_models
from apps.contacts.models import *
from apps.nodegraph.models import Node,NodeSet
from apps.smsforum.models import Village,Community

# helpers
def _contact(name, *grps):
    u=Contact(debug_id=name)
    u.save()
    for grp in grps:
        u.add_to_parent(grp)

    return u

def _group(name, *children):
    g=NodeSet(debug_id=name)
    g.save()
    g.add_children(*children)
    return g

class Worker(Contact):
    pass

class StealWorker(Worker):
    pass



class TestApp (TestScript):
    apps = (App, contacts_app.App)
 
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
        self.m_nodes = [_contact(n) for n in self.m_names]
        self.w_nodes = [_contact(n) for n in self.w_names]
        
        self.m_group = _group('men',*self.m_nodes)
        self.w_group = _group('women',*self.w_nodes)
        self.people_group = _group('people', self.m_group, self.w_group)
        
        self.people_group_unicode=u'people(men(matt,larry,jim,joe,mohammed),women(jen,julie,mary,fatou,sue)'

        self.backend=test.Backend(None)

    def testPerms(self):
        def printPerms(c):
            print "S: %s, R: %s, I: %s" % (c.perm_send, c.perm_receive, c.perm_ignore)
            
        print "Permission Test"
        c0=_contact('default')
        printPerms(c0)
        self.assertTrue(c0.perm_send and c0.perm_receive and not c0.perm_ignore)
        c0.perm_ignore=True
        printPerms(c0)
        c0.save()
        self.assertTrue(c0.perm_send and c0.perm_receive and c0.perm_ignore)
        c0.perm_send=False
        self.assertFalse(c0.perm_send)
        c0.perm_receive=False
        self.assertFalse(c0.perm_receive)
        c0.perm_send=True
        self.assertTrue(c0.perm_send)
        c0.perm_receive=True
        self.assertTrue(c0.perm_receive)
        c0.perm_ignore=False
        self.assertFalse(c0.perm_ignore)
        c0.perm_ignore=True
        self.assertTrue(c0.perm_ignore)

    def testLocales(self):
        print "\n\nLocale Test..."
        # TODO: Make these all asserts
        en='en_US'
        fr='fr_CA@euro'
        wo='wo_SN'
        es='es_AR'

        p1=self.m_nodes[0]
        p2=self.w_nodes[1]

        print p1.locale
        p1.locale=fr
        p1.save()
        self.assertTrue(p1.locale==fr)
        p1.locale=en
        self.assertTrue(p1.locale==en)
        p2.locale=wo
        p2.save()
        self.assertTrue(p1.locale==en and p2.locale==wo)

    def testDowncast(self):
        v=Village(name='v1')
        v.save()
        v.add_children(*self.m_nodes[0:2])
        print [o.__class__ for o in self.m_nodes[0].get_ancestors(klass=Village)]

        sw=StealWorker(debug_id='bob builder')
        sw.save()
        workers=NodeSet(debug_id='workers')
        workers.save()
        sw.add_to_parent(workers)

        print [o.__class__ for o in workers.flatten(klass=Worker)]
        print [o.__class__ for o in workers.flatten(klass=StealWorker)]


    def testFlattenTest(self):
        print "\nFlatten Test:"
        men_set=self.m_group.flatten()
#        self.assertTrue(men_set==frozenset(self.m_nodes))
        print men_set
        print frozenset(self.m_nodes)

        print "\nTry a group with a cycle:\n"
#        print self.cyclic_group.flatten()

    def testPrint(self):
        print "\nPrint Test:"
        out=unicode(self.people_group)
        self.assertTrue(out==self.people_group_unicode)
        print out

    """
    def testChannelConnectionFromMessage(self):
        print "\nPrint Channel Connection Test:"
        uid0='4156661212'
        uid1='6175551212'
        print "Can't run this until I figure out how to get an 'app' object set up properly in the test harness"

        con1=connection.Connection(self.backend,uid0)
        msg=message.Message(con1, 'test message')
        channel_con0=contacts_models.ChannelConnectionFromMessage(msg)

        "assert that the ChannelConnection's contact has the correct ID"
        self.assertTrue(channel_con0.contact.debug_id==uid0)

        # create a _different_ message on the same connection
        msg = message.Message(con1, 'Another Message')
        channel_con1=contacts_models.ChannelConnectionFromMessage(msg)

        # assert channel_connections are the SAME
        self.assertTrue(channel_con0==channel_con1)
    """ 






        
        
