from pypy.conftest import gettestobjspace

class AppTestDotnet:
    def setup_class(cls):
        space = gettestobjspace(usemodules=('clr',))
        cls.space = space

    def test_cliobject(self):
        import clr
        obj = clr._CliObject_internal('System.Collections.ArrayList', [])
        max_index = obj.call_method('Add', [42])
        assert max_index == 0

    def test_cache(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        ArrayList2 = clr.load_cli_class('System.Collections', 'ArrayList')
        assert ArrayList is ArrayList2

    def test_load_fail(self):
        import clr
        raises(ImportError, clr.load_cli_class, 'Foo', 'Bar')
        
    def test_ArrayList(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        obj = ArrayList()
        obj.Add(42)
        obj.Add(43)
        total = obj.get_Item(0) + obj.get_Item(1)
        assert total == 42+43

    def test_ArrayList_error(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        obj = ArrayList()
        raises(StandardError, obj.get_Item, 0)

    def test_float_conversion(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        obj = ArrayList()
        obj.Add(42.0)
        item = obj.get_Item(0)
        assert isinstance(item, float)

    def test_bool_conversion(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        obj = ArrayList()
        obj.Add(True)
        obj.Add(False)
        t = obj.get_Item(0)
        f = obj.get_Item(1)
        assert t and isinstance(t, bool)
        assert not f and isinstance(f, bool)
        obj.Add(42)
        assert obj.Contains(42)

    def test_getitem(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        obj = ArrayList()
        obj.Add(42)
        assert obj[0] == 42

    def test_property(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        obj = ArrayList()
        obj.Add(42)
        assert obj.Count == 1
        obj.Capacity = 10
        assert obj.Capacity == 10

    def test_unboundmethod(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        obj = ArrayList()
        ArrayList.Add(obj, 42)
        assert obj.get_Item(0) == 42

    def test_unboundmethod_typeerror(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        raises(TypeError, ArrayList.Add)
        raises(TypeError, ArrayList.Add, 0)

    def test_overload(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        obj = ArrayList()
        for i in range(10):
            obj.Add(i)
        assert obj.IndexOf(7) == 7
        assert obj.IndexOf(7, 0, 5) == -1

    def test_wrong_overload(self):
        import clr
        Math = clr.load_cli_class('System', 'Math')
        raises(TypeError, Math.Abs, "foo")

    def test_staticmethod(self):
        import clr
        Math = clr.load_cli_class('System', 'Math')
        res = Math.Abs(-42)
        assert res == 42
        assert type(res) is int
        res = Math.Abs(-42.0)
        assert res == 42.0
        assert type(res) is float

    def test_constructor_args(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        obj = ArrayList(42)
        assert obj.Capacity == 42

    def test_None_as_null(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        Hashtable = clr.load_cli_class('System.Collections', 'Hashtable')
        x = ArrayList()
        x.Add(None)
        assert x[0] is None
        y = Hashtable()
        assert y["foo"] is None

    def test_pass_opaque_arguments(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        class Foo:
            pass
        obj = Foo()
        x = ArrayList()
        x.Add(obj)
        obj2 = x[0]
        assert obj is obj2

    def test_string_wrapping(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        x = ArrayList()
        x.Add("bar")
        s = x[0]
        assert s == "bar"

    def test_static_property(self):
        import clr
        import os
        Environment = clr.load_cli_class('System', 'Environment')
        assert Environment.CurrentDirectory == os.getcwd()
        Environment.CurrentDirectory == '/'
        assert Environment.CurrentDirectory == os.getcwd()

    def test_GetEnumerator(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        x = ArrayList()
        enum = x.GetEnumerator()
        assert enum.MoveNext() is False

    def test_iteration(self):
        import clr
        ArrayList = clr.load_cli_class('System.Collections', 'ArrayList')
        x = ArrayList()
        x.Add(1)
        x.Add(2)
        x.Add(3)
        x.Add(4)
        sum = 0
        for i in x:
           sum += i
        assert sum == 1+2+3+4

    def test_iteration_stack(self):
        import clr
        Stack = clr.load_cli_class('System.Collections', 'Stack')
        obj = Stack()
        obj.Push(1)
        obj.Push(54)
        obj.Push(21)
        sum = 0
        for i in obj:
            sum += i
        assert sum == 1+54+21

    def test_load_generic_class(self):
        import clr
        ListInt = clr.load_cli_class("System.Collections.Generic", "List`1[System.Int32]")
        x = ListInt()
        x.Add(42)
        x.Add(4)
        x.Add(4)
        sum = 0
        for i in x:
           sum += i
        assert sum == 42+4+4

    def test_generic_class_typeerror(self):
        import clr
        ListInt = clr.load_cli_class("System.Collections.Generic", "List`1[System.Int32]")
        x = ListInt()
        raises(TypeError, x.Add, "test")

    def test_generic_dict(self):
        import clr
        genDictIntStr = clr.load_cli_class("System.Collections.Generic","Dictionary`2[System.Int32,System.String]")
        x = genDictIntStr()
        x[1] = "test"
        x[2] = "rest"
        assert x[1] == "test" 
        assert x[2] == "rest" 
        raises(TypeError, x.__setitem__, 3, 3)
        raises(TypeError, x.__setitem__, 4, 4.453)
        raises(TypeError, x.__setitem__, "test", 3)

