"""
Unary operations on SomeValues.
"""

from types import FunctionType
from pypy.annotation.pairtype import pair
from pypy.annotation.model import SomeObject, SomeInteger, SomeBool
from pypy.annotation.model import SomeString, SomeChar, SomeList, SomeDict
from pypy.annotation.model import SomeTuple, SomeImpossibleValue
from pypy.annotation.model import SomeInstance, SomeBuiltin 
from pypy.annotation.model import SomeIterator, SomePBC, new_or_old_class
from pypy.annotation.model import unionof, set, setunion, missing_operation
from pypy.annotation.factory import BlockedInference
from pypy.annotation.bookkeeper import getbookkeeper
from pypy.annotation.classdef import isclassdef

# convenience only!
def immutablevalue(x):
    return getbookkeeper().immutablevalue(x)

UNARY_OPERATIONS = set(['len', 'is_true', 'getattr', 'setattr', 'simple_call',
                        'iter', 'next'])

for opname in UNARY_OPERATIONS:
    missing_operation(SomeObject, opname)


class __extend__(SomeObject):
    
    def len(obj):
        return SomeInteger(nonneg=True)

    def is_true(obj):
        if obj.is_constant():
            return immutablevalue(bool(obj.const))
        else:
            s_len = obj.len()
            if s_len.is_constant():
                return immutablevalue(s_len.const > 0)
            else:
                return SomeBool()

    def getattr(obj, s_attr):
        # get a SomeBuiltin if the SomeObject has
        # a corresponding method to handle it
        if s_attr.is_constant() and isinstance(s_attr.const, str):
            attr = s_attr.const
            analyser = getattr(obj.__class__, 'method_' + attr, None)
            if analyser is not None:
                return SomeBuiltin(analyser, obj)
            # if the SomeObject is itself a constant, allow reading its attrs
            if obj.is_constant() and hasattr(obj.const, attr):
                return immutablevalue(getattr(obj.const, attr))
        return SomeObject()

    def bindcallables(obj, classdef):
        return obj   # default unbound __get__ implementation

    def simple_call(*obj_and_args):
        #raise Exception, "cannot follow simple_call%r" % (obj_and_args,)
        print "*** cannot follow simple_call%r" % (obj_and_args,)
        return SomeObject()


class __extend__(SomeBool):
    def is_true(self):
        return self

class __extend__(SomeTuple):

    def len(tup):
        return immutablevalue(len(tup.items))

    def iter(tup):
        return SomeIterator(unionof(*tup.items))

class __extend__(SomeDict):

    def len(dic):
        return immutablevalue(len(dic.items))


class __extend__(SomeList):

    def method_append(lst, s_value):
        pair(lst, SomeInteger()).setitem(s_value)

    def method_reverse(lst):
        pass

    def method_insert(lst, s_index, s_value):
        pair(lst, SomeInteger()).setitem(s_value)
        
    def method_pop(lst, s_index=None):
        return lst.s_item

    def iter(lst):
        return SomeIterator(lst.s_item)


class __extend__(SomeString):

    def method_join(str, s_list):
        return SomeString()

    def iter(str):
        return SomeIterator(SomeChar())


class __extend__(SomeChar):

    def len(chr):
        return immutablevalue(1)


class __extend__(SomeIterator):

    def next(itr):
        return itr.s_item


class __extend__(SomeInstance):

    def currentdef(ins):
        if ins.revision != ins.classdef.revision:
            #print ins.revision, ins.classdef.revision
            raise BlockedInference
        return ins.classdef

    def getattr(ins, s_attr):
        if s_attr.is_constant() and isinstance(s_attr.const, str):
            attr = s_attr.const
            #print 'getattr:', ins, attr, ins.classdef.revision
            s_result = ins.currentdef().find_attribute(attr).getvalue()
            # we call this because it might raise BlockedInference if
            # the above line caused generalization.
            ins.currentdef()
            return s_result
        return SomeObject()

    def setattr(ins, s_attr, s_value):
        if s_attr.is_constant() and isinstance(s_attr.const, str):
            attr = s_attr.const
            clsdef = ins.currentdef().locate_attribute(attr)
            attrdef = clsdef.attrs[attr]
            attrdef.readonly = False

            # if the attrdef is new, this must fail
            if attrdef.getvalue().contains(s_value):
                return
            # create or update the attribute in clsdef
            clsdef.generalize_attr(attr, s_value)
            raise BlockedInference
        return

    def contains(self, other):
        # override the default contains() to ignore revision numbers
        if self == other:
            return True
        s_union = pair(self, other).union()
        return (isinstance(s_union, SomeInstance) and
                s_union.classdef is self.classdef)


class __extend__(SomeBuiltin):
    def simple_call(bltn, *args):
        if bltn.s_self is not None:
            return bltn.analyser(bltn.s_self, *args)
        else:
            return bltn.analyser(*args)


class __extend__(SomePBC):

    def getattr(pbc, s_attr):
        bookkeeper = getbookkeeper()
        assert s_attr.is_constant()
        attr = s_attr.const
        actuals = []
        for c in pbc.prebuiltinstances:
            if hasattr(c, attr):
                # force the attribute to be considered on the class
                classdef = bookkeeper.getclassdef(new_or_old_class(c))
                classdef.find_attribute(attr).getvalue()
                # but only return the more precise result getattr(c, attr)
                actuals.append(immutablevalue(getattr(c, attr)))
        return unionof(*actuals)

    def setattr(pbc, s_attr, s_value):
        #raise Exception, "oops!"
        print "*** WARNING: setattr not wanted on %r" % pbc 
        pass

    def simple_call(pbc, *args):
        bookkeeper = getbookkeeper()
        results = []
        for func, classdef in pbc.prebuiltinstances.items():
            if isclassdef(classdef): 
                # create s_self and record the creation in the factory
                s_self = SomeInstance(classdef)
                classdef.instantiation_locations[
                    bookkeeper.position_key] = True
                results.append(bookkeeper.pycall(func, s_self, *args))
            else:
                results.append(bookkeeper.pycall(func, *args))
        return unionof(*results) 

    def bindcallables(pbc, classdef):   
        """ turn the callables in the given SomeCallable 'cal' 
            into bound versions.
        """
        d = {}
        for func, value in pbc.prebuiltinstances.items():
            if isinstance(func, FunctionType): 
                if isclassdef(value): 
                    print ("!!! rebinding an already bound"
                           " method %r with %r" % (func, value))
                d[func] = classdef
            elif isinstance(func, staticmethod):
                d[func.__get__(43)] = value
            else:
                d[func] = value 
        return SomePBC(d)

