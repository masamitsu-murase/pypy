
import autopath
import unittest


class AppTestCodeIntrospection:

    def test_attributes(self):
        def f(): pass
        def g(x, *y, **z): "docstring"
        assert hasattr(f.func_code, 'co_code')
        assert hasattr(g.func_code, 'co_code')

        testcases = [
            (f.func_code, {'co_name': 'f',
                           'co_names': (),
                           'co_varnames': (),
                           'co_argcount': 0,
                           'co_consts': (None,)
                           }),
            (g.func_code, {'co_name': 'g',
                           'co_names': (),
                           'co_varnames': ('x', 'y', 'z'),
                           'co_argcount': 1,
                           'co_consts': ("docstring", None),
                           }),
            ]

        import sys
        if sys.pypy_objspaceclass != 'TrivialObjSpace':
            testcases += [
                (abs.func_code, {'co_name': 'abs',
                                 'co_varnames': ('val',),
                                 'co_argcount': 1,
                                 'co_flags': 0,
                                 'co_consts': ("abs(number) -> number\n\nReturn the absolute value of the argument.",),
                                 }),
                (object.__init__.im_func.func_code,
                                {#'co_name': '__init__',   XXX getting descr__init__
                                 'co_varnames': ('obj', 'args', 'keywords'),
                                 'co_argcount': 1,
                                 'co_flags': 0x000C,  # VARARGS|VARKEYWORDS
                                 }),
                ]

        # in PyPy, built-in functions have code objects
        # that emulate some attributes
        for code, expected in testcases:
            assert hasattr(code, '__class__')
            assert not hasattr(code,'__dict__')
            for key, value in expected.items():
                assert getattr(code, key) == value

    def test_code(self):
        import sys, new
        if sys.pypy_objspaceclass == 'TrivialObjSpace':
            return   # skip
        codestr = "global c\na = 1\nb = 2\nc = a + b\n"
        ccode = compile(codestr, '<string>', 'exec')
        co = new.code(ccode.co_argcount,
                      ccode.co_nlocals,
                      ccode.co_stacksize,
                      ccode.co_flags,
                      ccode.co_code,
                      ccode.co_consts,
                      ccode.co_names,
                      ccode.co_varnames,
                      ccode.co_filename,
                      ccode.co_name,
                      ccode.co_firstlineno,
                      ccode.co_lnotab,
                      ccode.co_freevars,
                      ccode.co_cellvars)
        d = {}
        exec co in d
        assert d['c'] == 3
        # test backwards-compatibility version with no freevars or cellvars
        co = new.code(ccode.co_argcount,
                      ccode.co_nlocals,
                      ccode.co_stacksize,
                      ccode.co_flags,
                      ccode.co_code,
                      ccode.co_consts,
                      ccode.co_names,
                      ccode.co_varnames,
                      ccode.co_filename,
                      ccode.co_name,
                      ccode.co_firstlineno,
                      ccode.co_lnotab)
        d = {}
        exec co in d
        assert d['c'] == 3
