from rpython.translator.c.test.test_standalone import StandaloneTests
from rpython.config.translationoption import get_combined_translation_config
from pypy.config.pypyoption import get_pypy_config
from pypy.objspace.fake.checkmodule import checkmodule
from pypy.objspace.fake.objspace import FakeObjSpace
from pypy.module._hpy_universal.state import State

def test_checkmodule():
    def extra_func(space):
        state = space.fromcache(State)
        state.setup()

    rpython_opts = {'translation.gc': 'boehm'}
    # it isn't possible to ztranslate cpyext easily, so we check _hpy_universal
    # WITHOUT the cpyext parts
    pypy_opts = {'objspace.std.withliststrategies': False,
                 'objspace.hpy_cpyext_API': False}
    checkmodule('_hpy_universal',
                extra_func=extra_func,
                c_compile=True,
                rpython_opts=rpython_opts,
                pypy_opts=pypy_opts,
                show_pdbplus=False,
                )