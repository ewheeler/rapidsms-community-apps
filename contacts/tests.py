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

class Worker(Contact):
    pass

class StealWorker(Worker):
    pass



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
        
        self.people_group_unicode=u'people(men(matt,larry,jim,joe,mohammed),women(jen,julie,mary,fatou,sue)'

        self.backend=test.Backend(None)

    def testLocales(self):
        print "\n\nLocale Test..."
        # TODO: Make these all asserts
        en='en_US'
        fr='fr_CA@euro'
        wo='wo_SN'
        es='es_AR'

        p1=self.m_nodes[0]
        p2=self.w_nodes[1]

        print p1.locales
        print p1.locale
        p1.locale=fr
        print p1.locales
        print p1.locale
        p1.locale=en
        print p1.locales
        print p1.locale
        p1.add_locale(wo,1)
        p1.add_locale(fr,2)
        p1.add_locale(en,3)
        p1.add_locale(fr,4)
        print p1.locales
        print p1.locale
        p2.locale=wo
        print 'p2 %s' % p2.locales
        print 'p1 %s' % p1.locales

    def testDowncast(self):
        v=Village(name='v1')
        v.save()
        v._add_subnodes(*self.m_nodes[0:2])
        print [o.__class__ for o in self.m_nodes[0].get_ancestors(klass=Village)]

        sw=StealWorker(debug_id='bob builder')
        sw.save()
        workers=NodeSet(debug_id='workers')
        workers.save()
        sw.add_to_group(workers)

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

    def testChannelConnectionFromMessage(self):
        print "\nPrint Channel Connection Test:"
        uid0='4156661212'
        uid1='6175551212'

        con1=connection.Connection(self.backend,uid0)
        msg=message.Message(con1, 'test message')
        channel_con0=contacts_models.ChannelConnectionFromMessage(msg)

        # assert that the ChannelConnection's contact has the correct ID
        self.assertTrue(channel_con0.contact.debug_id==uid0)

        # create a _different_ message on the same connection
        msg = message.Message(con1, 'Another Message')
        channel_con1=contacts_models.ChannelConnectionFromMessage(msg)

        # assert channel_connections are the SAME
        self.assertTrue(channel_con0==channel_con1)

        
        pass
        
    def testSimulation(self):
        pass





        
        
