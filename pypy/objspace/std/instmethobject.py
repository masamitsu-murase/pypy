from __future__ import nested_scopes
from pypy.objspace.std.objspace import *


class W_InstMethObject(object):
    def __init__(w_self, w_im_self,w_im_func):
        w_self.w_im_self = w_im_self
        w_self.w_im_func = w_im_func


#def function_unwrap(space, w_function):
#    # XXX this is probably a temporary hack
#    def proxy_function(*args, **kw):
#        w_arguments = space.wrap(args)
#        w_keywords  = space.wrap(kw)
#        w_result = func_call(space, w_function, w_arguments, w_keywords)
#        return space.unwrap(w_result)
#    # XXX no closure implemented
#    return proxy_function
#
#StdObjSpace.unwrap.register(function_unwrap, W_FuncObject)


def instmeth_call(space, w_instmeth, w_arguments, w_keywords):
    w_args = space.add(space.newtuple([self.w_im_self]),
                       w_arguments)
    w_ret = space.call(self.w_im_func, w_args, w_keywords)
    return w_ret

StdObjSpace.call.register(instmeth_call, W_InstMeth, W_ANY, W_ANY)
