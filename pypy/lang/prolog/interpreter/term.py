import math
from pypy.rlib.objectmodel import we_are_translated, UnboxedValue
from pypy.rlib.rarithmetic import intmask
from pypy.lang.prolog.interpreter.error import UnificationFailed, UncatchableError
from pypy.rlib.jit import hint
from pypy.rlib.objectmodel import specialize

DEBUG = False

TAGBITS = 3
CURR_TAG = 1
def tag():
    global CURR_TAG
    CURR_TAG += 1
    assert CURR_TAG <= 2 ** TAGBITS
    return CURR_TAG

def debug_print(*args):
    if DEBUG and not we_are_translated():
        print " ".join([str(a) for a in args])

def pure_hash_function(s):
    return hash(s)
pure_hash_function._pure_function_ = True

class PrologObject(object):
    __slots__ = ()
    _immutable_ = True

    def __init__(self):
        raise NotImplementedError("abstract base class")
        return self

    def getvalue(self, heap):
        return self

    def dereference(self, heap):
        raise NotImplementedError("abstract base class")

    def get_max_var(self):
        return -1

    def copy(self, heap, memo):
        raise NotImplementedError("abstract base class")

    def copy_and_unify(self, other, heap, memo):
        raise NotImplementedError("abstract base class")

    def clone_compress_vars(self, vars_new_indexes, offset):
        return self

    def get_unify_hash(self):
        # if two non-var objects return two different numbers
        # they must not be unifiable
        raise NotImplementedError("abstract base class")

    def unify_hash_of_child(self, i):
        raise KeyError

    @specialize.arg(3)
    def unify(self, other, heap, occurs_check=False):
        raise NotImplementedError("abstract base class")

    @specialize.arg(3)
    def _unify(self, other, heap, occurs_check=False):
        raise NotImplementedError("abstract base class")

    def contains_var(self, var, heap):
        return False

    def __eq__(self, other):
        # for testing
        return (self.__class__ == other.__class__ and
                self.__dict__ == other.__dict__)

    def __ne__(self, other):
        # for testing
        return not (self == other)


class Var(PrologObject):
    TAG = 0
    STANDARD_ORDER = 0

    __slots__ = ('index', )
    cache = {}
    _immutable_ = True

    def __init__(self, index):
        self.index = index

    @specialize.arg(3)
    def unify(self, other, heap, occurs_check=False):
        return self.dereference(heap)._unify(other, heap, occurs_check)

    @specialize.arg(3)
    def _unify(self, other, heap, occurs_check=False):
        other = other.dereference(heap)
        if isinstance(other, Var) and other is self:
            pass
        elif occurs_check and other.contains_var(self, heap):
            raise UnificationFailed()
        else:
            heap.setvar(self.index, other)

    def dereference(self, heap):
        next = heap.getvar(self.index)
        if next is None:
            return self
        else:
            result = next.dereference(heap)
            # do path compression
            heap.setvar(self.index, result)
            return result

    def getvalue(self, heap):
        res = self.dereference(heap)
        if not isinstance(res, Var):
            return res.getvalue(heap)
        return res

    def copy(self, heap, memo):
        hint(self, concrete=True)
        try:
            return memo[self]
        except KeyError:
            newvar = memo[self] = heap.newvar()
            return newvar

    def copy_and_unify(self, other, heap, memo):
        hint(self, concrete=True)
        self = hint(self, deepfreeze=True)
        try:
            seen_value = memo[self]
        except KeyError:
            memo[self] = other
            return other
        else:
            seen_value.unify(other, heap)
            return seen_value


    def get_max_var(self):
        return self.index

    def clone_compress_vars(self, vars_new_indexes, offset):
        if self.index in vars_new_indexes:
            return Var.newvar(vars_new_indexes[self.index])
        index = len(vars_new_indexes) + offset
        vars_new_indexes[self.index] = index
        return Var.newvar(index)
    
    def get_unify_hash(self):
        return 0

    def contains_var(self, var, heap):
        self = self.dereference(heap)
        if self is var:
            return True
        if not isinstance(self, Var):
            return self.contains_var(var, heap)
        return False

    def __repr__(self):
        return "Var(%s)" % (self.index, )


    def __eq__(self, other):
        # for testing
        return (self.__class__ == other.__class__ and
                self.index == other.index)

    def newvar(index):
        result = Var.cache.get(index, None)
        if result is not None:
            return result
        Var.cache[index] = result = Var(index)
        return result
    newvar = staticmethod(newvar)


class NonVar(PrologObject):
    __slots__ = ()

    def dereference(self, heap):
        return self

    @specialize.arg(3)
    def unify(self, other, heap, occurs_check=False):
        return self._unify(other, heap, occurs_check)


    @specialize.arg(3)
    def basic_unify(self, other, heap, occurs_check=False):
        raise NotImplementedError("abstract base class")

    @specialize.arg(3)
    def _unify(self, other, heap, occurs_check=False):
        other = other.dereference(heap)
        if isinstance(other, Var):
            other._unify(self, heap, occurs_check)
        else:
            self.basic_unify(other, heap, occurs_check)

    def copy_and_unify(self, other, heap, memo):
        other = other.dereference(heap)
        if isinstance(other, Var):
            copy = self.copy(heap, memo)
            other._unify(copy, heap)
            return copy
        else:
            return self.copy_and_basic_unify(other, heap, memo)

    def copy_and_basic_unify(self, other, heap, memo):
        raise NotImplementedError("abstract base class")


class Callable(NonVar):
    __slots__ = ("name", "signature")
    name = ""
    signature = ""

    def get_prolog_signature(self):
        raise NotImplementedError("abstract base")


class Atom(Callable):
    TAG = tag()
    STANDARD_ORDER = 1

    cache = {}
    _immutable_ = True

    def __init__(self, name):
        self.name = name
        self.signature = self.name + "/0"

    def __str__(self):
        return self.name

    def __repr__(self):
        return "Atom(%r)" % (self.name,)

    @specialize.arg(3)
    def basic_unify(self, other, heap, occurs_check=False):
        if isinstance(other, Atom) and (self is other or
                                        other.name == self.name):
            return
        raise UnificationFailed

    def copy(self, heap, memo):
        return self

    def copy_and_basic_unify(self, other, heap, memo):
        hint(self, concrete=True)
        if isinstance(other, Atom) and (hint(self is other, promote=True) or
                                        other.name == self.name):
            return self
        else:
            raise UnificationFailed

    def get_unify_hash(self):
        name = hint(self.name, promote=True)
        return intmask(pure_hash_function(name) << TAGBITS | self.TAG)

    def get_prolog_signature(self):
        return Term("/", [self, NUMBER_0])

    def newatom(name):
        result = Atom.cache.get(name, None)
        if result is not None:
            return result
        Atom.cache[name] = result = Atom(name)
        return result
    newatom = staticmethod(newatom)


class Number(NonVar):
    TAG = tag()
    STANDARD_ORDER = 2
    _immutable_ = True
    def __init__(self, num):
        self.num = num

    @specialize.arg(3)
    def basic_unify(self, other, heap, occurs_check=False):
        if isinstance(other, Number) and other.num == self.num:
            return
        raise UnificationFailed

    def copy(self, heap, memo):
        return self

    def copy_and_basic_unify(self, other, heap, memo):
        hint(self, concrete=True)
        if isinstance(other, Number) and other.num == self.num:
            return self
        else:
            raise UnificationFailed

    def __str__(self):
        return repr(self.num)

    def __repr__(self):
        return "Number(%r)" % (self.num, )

    def get_unify_hash(self):
        return intmask(self.num << TAGBITS | self.TAG)

NUMBER_0 = Number(0)

class Float(NonVar):
    TAG = tag()
    STANDARD_ORDER = 2
    _immutable_ = True
    def __init__(self, num):
        self.num = num

    @specialize.arg(3)
    def basic_unify(self, other, heap, occurs_check=False):
        if isinstance(other, Float) and other.num == self.num:
            return
        raise UnificationFailed

    def copy(self, heap, memo):
        return self

    def copy_and_basic_unify(self, other, heap, memo):
        hint(self, concrete=True)
        if isinstance(other, Float) and other.num == self.num:
            return self
        else:
            raise UnificationFailed

    def get_unify_hash(self):
        #XXX no clue whether this is a good idea...
        m, e = math.frexp(self.num)
        m = intmask(int(m / 2 * 2 ** (32 - TAGBITS)))
        return intmask(m << TAGBITS | self.TAG)

    def __str__(self):
        return repr(self.num)

    def __repr__(self):
        return "Float(%r)" % (self.num, )

class BlackBox(NonVar):
    # meant to be subclassed
    TAG = tag()
    STANDARD_ORDER = 4
    def __init__(self):
        pass

    @specialize.arg(3)
    def basic_unify(self, other, heap, occurs_check=False):
        if self is other:
            return
        raise UnificationFailed

    def copy(self, heap, memo):
        return self

    def copy_and_basic_unify(self, other, heap, memo):
        hint(self, concrete=True)
        if self is other:
            return self
        else:
            raise UnificationFailed

    def get_unify_hash(self):
        return intmask(id(self) << TAGBITS | self.TAG)


# helper functions for various Term methods

def _clone(obj, offset):
    return obj.clone(offset)

def _clone_compress_vars(obj, vars_new_indexes, offset):
    return obj.clone_compress_vars(vars_new_indexes, offset)

def _getvalue(obj, heap):
    return obj.getvalue(heap)

class Term(Callable):
    TAG = tag()
    STANDARD_ORDER = 3
    _immutable_ = True
    def __init__(self, name, args, signature=None):
        self.name = name
        self.args = args
        if signature is None:
            self.signature = name + "/" + str(len(args))
        else:
            self.signature = signature

    def __repr__(self):
        return "Term(%r, %r)" % (self.name, self.args)

    def __str__(self):
        return "%s(%s)" % (self.name, ", ".join([str(a) for a in self.args]))

    @specialize.arg(3)
    def basic_unify(self, other, heap, occurs_check=False):
        if (isinstance(other, Term) and
            self.name == other.name and
            len(self.args) == len(other.args)):
            for i in range(len(self.args)):
                self.args[i].unify(other.args[i], heap, occurs_check)
        else:
            raise UnificationFailed

    def copy(self, heap, memo):
        hint(self, concrete=True)
        self = hint(self, deepfreeze=True)
        newargs = []
        i = 0
        while i < len(self.args):
            hint(i, concrete=True)
            arg = self.args[i].copy(heap, memo)
            newargs.append(arg)
            i += 1
        return Term(self.name, newargs, self.signature)

    def copy_and_basic_unify(self, other, heap, memo):
        hint(self, concrete=True)
        self = hint(self, deepfreeze=True)
        if (isinstance(other, Term) and
            self.signature == other.signature):
            newargs = [None] * len(self.args)
            i = 0
            while i < len(self.args):
                hint(i, concrete=True)
                arg = self.args[i].copy_and_unify(other.args[i], heap, memo)
                newargs[i] = arg
                i += 1
            return Term(self.name, newargs, self.signature)
        else:
            raise UnificationFailed

    def get_max_var(self):
        result = -1
        for subterm in self.args:
            result = max(result, subterm.get_max_var())
        return result
    
    def clone_compress_vars(self, vars_new_indexes, offset):
        return self._copy_term(_clone_compress_vars, vars_new_indexes, offset)

    def getvalue(self, heap):
        return self._copy_term(_getvalue, heap)

    def _copy_term(self, copy_individual, *extraargs):
        args = [None] * len(self.args)
        newinstance = False
        for i in range(len(self.args)):
            arg = self.args[i]
            cloned = copy_individual(arg, *extraargs)
            if cloned is not arg:
                newinstance = True
            args[i] = cloned
        if newinstance:
            return Term(self.name, args, self.signature)
        else:
            return self

    def get_unify_hash(self):
        signature = hint(self.signature, promote=True)
        return intmask(pure_hash_function(signature) << TAGBITS | self.TAG)

    def unify_hash_of_child(self, i):
        return self.args[i].get_unify_hash()

    def get_prolog_signature(self):
        return Term("/", [Atom.newatom(self.name), Number(len(self.args))])
    
    def contains_var(self, var, heap):
        for arg in self.args:
            if arg.contains_var(var, heap):
                return True
        return False
        

class Rule(object):
    _immutable_ = True
    unify_hash = []
    def __init__(self, head, body):
        from pypy.lang.prolog.interpreter import helper
        d = {}
        head = head.clone_compress_vars(d, 0)
        assert isinstance(head, Callable)
        self.head = head
        if body is not None:
            body = helper.ensure_callable(body)
            self.body = body.clone_compress_vars(d, 0)
        else:
            self.body = None
        self.numvars = len(d)
        self.signature = self.head.signature
        if isinstance(head, Term):
            self.unify_hash = [arg.get_unify_hash() for arg in head.args]
        self._does_contain_cut()

    def _does_contain_cut(self):
        if self.body is None:
            self.contains_cut = False
            return
        stack = [self.body]
        while stack:
            current = stack.pop()
            if isinstance(current, Atom):
                if current.name == "!":
                    self.contains_cut = True
                    return
            elif isinstance(current, Term):
                stack.extend(current.args)
        self.contains_cut = False

    def clone_and_unify_head(self, heap, head):
        memo = {}
        h2 = self.head
        hint(h2, concrete=True)
        if isinstance(h2, Term):
            assert isinstance(head, Term)
            i = 0
            while i < len(h2.args):
                i = hint(i, concrete=True)
                arg2 = h2.args[i]
                arg1 = head.args[i]
                arg2.copy_and_unify(arg1, heap, memo)
                i += 1
        body = self.body
        hint(body, concrete=True)
        if body is None:
            return None
        return body.copy(heap, memo)

    def __repr__(self):
        if self.body is None:
            return "%s." % (self.head, )
        return "%s :- %s." % (self.head, self.body)


@specialize.argtype(0)
def rcmp(a, b): # RPython does not support cmp...
    if a == b:
        return 0
    if a < b:
        return -1
    return 1

def cmp_standard_order(obj1, obj2, heap):
    c = rcmp(obj1.STANDARD_ORDER, obj2.STANDARD_ORDER)
    if c != 0:
        return c
    if isinstance(obj1, Var):
        assert isinstance(obj2, Var)
        return rcmp(obj1.index, obj2.index)
    if isinstance(obj1, Atom):
        assert isinstance(obj2, Atom)
        return rcmp(obj1.name, obj2.name)
    if isinstance(obj1, Term):
        assert isinstance(obj2, Term)
        c = rcmp(len(obj1.args), len(obj2.args))
        if c != 0:
            return c
        c = rcmp(obj1.name, obj2.name)
        if c != 0:
            return c
        for i in range(len(obj1.args)):
            a1 = obj1.args[i].dereference(heap)
            a2 = obj2.args[i].dereference(heap)
            c = cmp_standard_order(a1, a2, heap)
            if c != 0:
                return c
        return 0
    # XXX hum
    if isinstance(obj1, Number):
        if isinstance(obj2, Number):
            return rcmp(obj1.num, obj2.num)
        elif isinstance(obj2, Float):
            return rcmp(obj1.num, obj2.num)
    if isinstance(obj1, Float):
        if isinstance(obj2, Number):
            return rcmp(obj1.num, obj2.num)
        elif isinstance(obj2, Float):
            return rcmp(obj1.num, obj2.num)
    assert 0
