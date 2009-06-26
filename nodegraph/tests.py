from rapidsms.tests.scripted import TestScript
from app import App
import apps.nodegraph.app as nodegraph_app
from apps.nodegraph.models import Node, NodeSet

# helpers
class Person(Node):
    pass

class Town(NodeSet):
    pass

def _u(name, *grps):
    u=Person(debug_id=name)
    u.save()
    for grp in grps:
        u.add_to_parent(grp)

    return u

def _g(name, *children):
    g=Town(debug_id=name)
    g.save()
    g.add_children(*children)
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
    girl_names = ['jennie','sue-y']
    boy_names = ['johnny', 'jimmie']

    def setUp(self):
        TestScript.setUp(self)
        self.men = [_u(m) for m in self.m_names]
        self.women = [_u(m) for m in self.w_names]
        self.men_grp = _g('men', *self.men)
        self.women_grp = _g('women', *self.women)
        self.m_w_grp=_g('men_and_women', self.women_grp, self.men_grp)
        self.people_grp=_g('people',self.men_grp,self.women_grp,self.m_w_grp)

    def tearDown(self):
        self.men_grp.delete()
        self.women_grp.delete()
        self.m_w_grp.delete()
        self.people_grp.delete()
        for m in self.men:
            m.delete()

        for w in self.women:
            w.delete()

        TestScript.tearDown(self)
        
        
    def testNode(self):
        print self.men_grp
        print self.men_grp.flatten(klass=Person)
        print self.people_grp
        print self.people_grp.flatten()
        self.assertTrue(self.people_grp._downcast(klass=basestring) is None)
        self.assertTrue(isinstance( \
                self.people_grp.children[0]._downcast(klass=Town),
                Town))
