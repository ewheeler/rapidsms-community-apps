from rapidsms.tests.scripted import TestScript
from app import App
import apps.nodegraph.app as nodegraph_app
from apps.nodegraph.models import Node, NodeSet

# helpers
def _user(name, *grps):
    u=Node(debug_id=name)
    u.save()
    for grp in grps:
        u.add_to_parent(grp)

    return u

def _group(name, *children):
    g=NodeSet(debug_id=name)
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
            
        # make some nodes and graphs
        # imagine this is users and groups for clarity
        self.m_nodes = [_user(n) for n in self.m_names]
        self.w_nodes = [_user(n) for n in self.w_names]
        self.girl_nodes = [_user(n) for n in self.girl_names]
        self.boy_nodes = [_user(n) for n in self.boy_names]
        
        self.m_group = _group('men',*self.m_nodes)
        self.w_group = _group('women',*self.w_nodes)
        self.g_group = _group('girls',*self.girl_nodes)
        self.g_group.add_to_parent(self.w_group)
        self.b_group = _group('boys',*self.boy_nodes)
        self.b_group.add_to_parent(self.m_group)

        self.people_group = _group('people', self.m_group, self.w_group)

        # set up Cyclic(A(B(*A,woman),man))
        self.cyc_a=_group('a',self.m_nodes[0])
        self.cyc_b=_group('b',self.cyc_a,self.w_nodes[0])
        self.cyc_a.add_children(self.cyc_b)
        self.cyclic_group=_group('cyclic',self.cyc_a)
               
        # simple tree 
        self.leaf1=_user('leaf1')
        self.leaf2=_user('leaf2')
        self.simple_tree=_group('tree', _group('L1',_group('L2',self.leaf1, _group('L3',self.leaf2))))
        
    def testNode(self):
#        print self.people_group
#        print self.cyclic_group
#        print self.cyclic_group.flatten()
#        print dir(NodeSet)
        print


        print self.m_nodes[0].get_ancestors(1)
        
        print

        


        skiers=_group('skiers', self.m_group.childleaves[1])
        snowbs=_group('snowboarders', self.m_group.childleaves[1], *self.w_group.childleaves[0:2])
        sporty=_group('sporty',skiers,snowbs,self.people_group)
        sporty.add_to_parent(self.people_group)
        sporty.remove_from_parent(self.people_group)

        tb=_user('tranny boy',self.people_group)
        print self.people_group.flatten()
        print self.people_group.flatten(max_depth=1)
        print self.people_group.flatten()
        self.w_group.remove_from_parent(self.people_group)
        self.m_group.childleaves[0].remove_from_parent(self.m_group)
        print self.people_group.flatten()

        docs=_group('docs', *self.m_nodes[0:2])
        peds=_group('pediatricians', *self.w_nodes[1:3])
        peds.add_to_parent(docs)
        docs.add_children(*self.w_nodes[2:])
        docs.add_to_parent(peds)

        skiers.add_to_parent(self.m_group)
        sporty.add_to_parent(skiers)
        snowbs.add_to_parent(self.w_group)
        print docs
        print self.people_group





        
        
