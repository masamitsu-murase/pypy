
""" test transparent proxy features
"""

class AppTestProxy(object):
    def setup_method(self, meth):
        self.w_Controller = self.space.appexec([], """():
        class Controller(object):
            def __init__(self, obj):
                self.obj = obj
    
            def perform(self, name, *args):
                return getattr(self.obj, name)(*args)
        return Controller
        """)
    
    def test_proxy(self):
        lst = proxy(list, lambda : None)
        assert type(lst) is list

    def test_proxy_repr(self):
        def controller(name, *args):
            lst = [1,2,3]
            if name == '__repr__':
                return repr(lst)
        
        lst = proxy(list, controller)
        assert repr(lst) == repr([1,2,3])

    def test_proxy_append(self):
        c = self.Controller([])
        lst = proxy(list, c.perform)
        lst.append(1)
        lst.append(2)
        assert repr(lst) == repr([1,2])

    def test_gt_lt_list(self):
        c = self.Controller([])
        lst = proxy(list, c.perform)
        lst.append(1)
        lst.append(2)
        assert lst < [1,2,3]
        assert [1,2,3] > lst
        #assert not ([2,3] < lst)
        assert [2,3] >= lst
        assert lst <= [1,2]
