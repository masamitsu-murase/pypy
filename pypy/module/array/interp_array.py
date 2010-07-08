from pypy.interpreter.baseobjspace import Wrappable
from pypy.interpreter.error import OperationError
from pypy.interpreter.typedef import TypeDef, GetSetProperty
from pypy.rpython.lltypesystem import lltype, rffi
from pypy.interpreter.gateway import interp2app, ObjSpace, W_Root, ApplevelClass
from pypy.rlib.jit import dont_look_inside
from pypy.rlib import rgc
from pypy.rlib.unroll import unrolling_iterable
from pypy.rlib.rstruct.runpack import runpack

import os, types, re
path, _ = os.path.split(__file__)
app_array = os.path.join(path, 'app_array.py')
app = ApplevelClass(file(app_array).read())

def appmethod(n,allappfn={}):
    if not allappfn.has_key(n):
        #exec 'import %s as mod'%f.__module__
        #src=file(re.sub('.pyc$', '.py', mod.__file__)).read()
        #app = ApplevelClass(src)
        import app_array
        f=getattr(app_array,n)
        args = f.func_code.co_varnames[0:f.func_code.co_argcount]
        args = ', '.join(['space'] + ['w_'+s for s in args])
        appfn = app.interphook(n)
        exec """def descr(%s):
                    return appfn(%s)"""%(args, args) in locals()
        descr.__name__='descr_appmethod_%s'%n
        allappfn[n]=interp2app(descr)
    return allappfn[n]

class W_ArrayBase(Wrappable):
    pass

class TypeCode(object):
    def __init__(self, itemtype, unwrap, canoverflow=False, signed=False):
        self.itemtype = itemtype
        self.bytes = rffi.sizeof(itemtype)
        #self.arraytype = lltype.GcArray(itemtype)
        self.arraytype = lltype.Array(itemtype, hints={'nolength': True})
        self.unwrap = unwrap
        self.signed = signed
        self.canoverflow = canoverflow
        self.w_class = None


    def _freeze_(self):
        # hint for the annotator: track individual constant instances 
        return True


types = {
    'c': TypeCode(lltype.Char,        'str_w'),
    'u': TypeCode(lltype.UniChar,     'unicode_w'),
    'b': TypeCode(rffi.SIGNEDCHAR,    'int_w', True, True),
    'B': TypeCode(rffi.UCHAR,         'int_w', True),
    'h': TypeCode(rffi.SHORT,         'int_w', True, True),
    'H': TypeCode(rffi.USHORT,        'int_w', True),
    'i': TypeCode(rffi.INT,           'int_w', True, True),
    'I': TypeCode(rffi.UINT,          'int_w', True), 
    'l': TypeCode(rffi.LONG,          'int_w', True, True),
    'L': TypeCode(rffi.ULONG,         'bigint_w'), # Overflow handled by rbigint.touint() which
                                                   # corresponds to the C-type unsigned long
    'f': TypeCode(lltype.SingleFloat, 'float_w'),
    'd': TypeCode(lltype.Float,       'float_w'),
    }
for k, v in types.items(): v.typecode=k
unroll_typecodes = unrolling_iterable(types.keys())

def make_array(mytype):
    class W_Array(W_ArrayBase):
        itemsize=mytype.bytes
        typecode=mytype.typecode
        def __init__(self, space):
            self.space = space
            self.len = 0
            self.buffer = lltype.nullptr(mytype.arraytype)

        def item_w(self, w_item):
            space = self.space
            unwrap = getattr(space, mytype.unwrap)
            item = unwrap(w_item)
            if mytype.unwrap == 'bigint_w':
                try:
                    item = item.touint()
                except (ValueError, OverflowError):
                    msg = 'unsigned %d-byte integer out of range' % mytype.bytes
                    raise OperationError(space.w_OverflowError, space.wrap(msg))
            elif mytype.unwrap == 'str_w' or mytype.unwrap == 'unicode_w':
                if len(item) != 1:
                    msg = 'array item must be char'
                    raise OperationError(space.w_TypeError, space.wrap(msg))
                item=item[0]

            if mytype.canoverflow:
                msg = None
                if mytype.signed:
                    if item < -1 << (mytype.bytes * 8 - 1):
                        msg = 'signed %d-byte integer is less than minimum' % mytype.bytes
                    elif item > (1 << (mytype.bytes * 8 - 1)) - 1:
                        msg = 'signed %d-byte integer is greater than maximum' % mytype.bytes
                else:
                    if item < 0:
                        msg = 'unsigned %d-byte integer is less than minimum' % mytype.bytes
                    elif item > (1 << (mytype.bytes * 8)) - 1:
                        msg = 'unsigned %d-byte integer is greater than maximum' % mytype.bytes
                if msg is not None:
                    raise OperationError(space.w_OverflowError, space.wrap(msg))
            return rffi.cast(mytype.itemtype, item)


        def __del__(self):
            self.setlen(0)

                
        def setlen(self, size):
            if size > 0:
                #new_buffer = lltype.malloc(mytype.arraytype, size)
                new_buffer = lltype.malloc(mytype.arraytype, size, flavor='raw')
                for i in range(min(size,self.len)):
                    new_buffer[i] = self.buffer[i]
            else:
                new_buffer = lltype.nullptr(mytype.arraytype)
            if self.buffer != lltype.nullptr(mytype.arraytype):
                lltype.free(self.buffer, flavor='raw')                
            self.buffer = new_buffer
            self.len = size
        setlen.unwrap_spec = ['self', int]

        def descr_len(self):
            return self.space.wrap(self.len)
        descr_len.unwrap_spec = ['self']


        def descr_getitem(self, w_idx):
            space=self.space
            start, stop, step = space.decode_index(w_idx, self.len)
            if step==0:
                item = self.buffer[start]
                tc=mytype.typecode
                if tc == 'b' or tc == 'B' or tc == 'h' or tc == 'H' or tc == 'i' or tc == 'l':
                    item = rffi.cast(lltype.Signed, item)
                elif mytype.typecode == 'f':
                    item = float(item)
                return self.space.wrap(item)
            else:
                size = (stop - start) / step
                if (stop - start) % step > 0: size += 1
                w_a=mytype.w_class(self.space)
                w_a.setlen(size)
                j=0
                for i in range(start, stop, step):
                    w_a.buffer[j]=self.buffer[i]
                    j+=1
                return w_a
        descr_getitem.unwrap_spec = ['self', W_Root]


        def descr_append(self, w_x):
            x = self.item_w(w_x)
            self.setlen(self.len + 1)
            self.buffer[self.len - 1] = x
        descr_append.unwrap_spec = ['self', W_Root]


        def descr_fromsequence(self, w_seq):
            space = self.space
            w_new = space.call_function(space.getattr(w_seq, space.wrap('__len__')))
            new = space.int_w(w_new)
            oldlen = self.len
            self.setlen(self.len + new)
            for i in range(new):
                w_item = space.call_function(
                    space.getattr(w_seq, space.wrap('__getitem__')),
                    space.wrap(i))
                try:
                    item=self.item_w(w_item)
                except OperationError:
                    self.setlen(oldlen + i)
                    raise
                self.buffer[oldlen + i ] = item
        descr_fromsequence.unwrap_spec = ['self', W_Root]


        def descr_extend(self, w_iterable):
            space=self.space
            if isinstance(w_iterable, W_ArrayBase):
                if mytype.typecode != w_iterable.typecode:
                    msg = "can only extend with array of same kind"
                    raise OperationError(space.w_TypeError, space.wrap(msg))
            w_iterator = space.iter(w_iterable)
            while True:
                try:
                    w_item = space.next(w_iterator)
                except OperationError, e:
                    if not e.match(space, space.w_StopIteration):
                        raise
                    break
                self.descr_append(w_item)
        descr_extend.unwrap_spec = ['self', W_Root]


        def descr_setitem(self, w_idx, w_item):
            start, stop, step = self.space.decode_index(w_idx, self.len)
            if step==0:
                item = self.item_w(w_item)
                self.buffer[start] = item
            else:
                if isinstance(w_item, W_Array): # Implies mytype.typecode == w_item.typecode
                    size = (stop - start) / step
                    if (stop - start) % step > 0: size += 1
                    if w_item.len != size: # FIXME: Support for step=1
                        msg = ('attempt to assign array of size %d to ' + 
                               'slice of size %d') % (w_item.len, size)
                        raise OperationError(self.space.w_ValueError,
                                             self.space.wrap(msg))
                    j=0
                    for i in range(start, stop, step):
                        self.buffer[i]=w_item.buffer[j]
                        j+=1
                    return
                msg='can only assign array to array slice'
                raise OperationError(self.space.w_TypeError, self.space.wrap(msg))
        descr_setitem.unwrap_spec = ['self', W_Root, W_Root]

        def descr_fromstring(self, s):
            if len(s)%mytype.bytes !=0:
                msg = 'string length not a multiple of item size'
                raise OperationError(self.space.w_ValueError, self.space.wrap(msg))
            oldlen = self.len
            new = len(s) / mytype.bytes
            self.setlen(oldlen + new)
            if False:
                for i in range(new):
                    p = i * mytype.bytes
                    item=runpack(mytype.typecode, s[p:p + mytype.bytes])
                    #self.buffer[oldlen + i]=self.item_w(self.space.wrap(item))
                    self.buffer[oldlen + i]=rffi.cast(mytype.itemtype, item)
            else:
                pbuf = rffi.cast(rffi.CCHARP, self.buffer)
                for i in range(len(s)):
                    pbuf[oldlen * mytype.bytes + i] = s[i]
                    
        descr_fromstring.unwrap_spec = ['self', str]

        def descr_tolist(self):
            w_l=self.space.newlist([])
            for i in range(self.len):
                w_l.append(self.descr_getitem(self.space.wrap(i)))
            return w_l
            #return self.space.newlist([self.space.wrap(i) for i in self.buffer])
        descr_tolist.unwrap_spec = ['self']

        def descr_tostring(self):
            pbuf = rffi.cast(rffi.CCHARP, self.buffer)
            s = ''
            i=0
            while i < self.len * self.itemsize:
                s += pbuf[i]
                i+=1
            return self.space.wrap(s)

        def descr_buffer(self):
            from pypy.interpreter.buffer import StringLikeBuffer
            space = self.space
            return space.wrap(StringLikeBuffer(space, self.descr_tostring()))
        descr_buffer.unwrap_spec = ['self']

        def descr_isarray(self, w_other):
            return self.space.wrap(isinstance(w_other, W_ArrayBase))

        def descr_reduce(self):
            space=self.space
            if self.len>0:
                args=[space.wrap(self.typecode), self.descr_tostring()]
            else:
                args=[space.wrap(self.typecode)]
            from pypy.interpreter.mixedmodule import MixedModule
            w_mod    = space.getbuiltinmodule('array')
            mod      = space.interp_w(MixedModule, w_mod)
            w_new_inst = mod.get('array')
            return space.newtuple([w_new_inst, space.newtuple(args)])



    def descr_itemsize(space, self):
        return space.wrap(self.itemsize)
    def descr_typecode(space, self):
        return space.wrap(self.typecode)

    W_Array.__name__ = 'W_ArrayType_'+mytype.typecode
    W_Array.typedef = TypeDef(
        'ArrayType_'+mytype.typecode,
        append       = interp2app(W_Array.descr_append),
        __len__      = interp2app(W_Array.descr_len),
        __getitem__  = interp2app(W_Array.descr_getitem),
        __setitem__  = interp2app(W_Array.descr_setitem),

        itemsize     = GetSetProperty(descr_itemsize, cls=W_Array),
        typecode     = GetSetProperty(descr_typecode, cls=W_Array),
        extend       = interp2app(W_Array.descr_extend),

        _fromsequence= interp2app(W_Array.descr_fromsequence),
        fromstring   = interp2app(W_Array.descr_fromstring),
        fromunicode  = appmethod('fromunicode'),
        fromfile     = appmethod('fromfile'),
        read         = appmethod('fromfile'),
        _fromfile    = appmethod('_fromfile'),
        fromlist     = appmethod('fromlist'),
        
        tolist       = interp2app(W_Array.descr_tolist),
        tounicode    = appmethod('tounicode'),
        tofile       = appmethod('tofile'),
        write        = appmethod('tofile'),
        #tostring     = appmethod('tostring'),
        tostring     = interp2app(W_Array.descr_tostring),

        _setlen      = interp2app(W_Array.setlen),
        __buffer__   = interp2app(W_Array.descr_buffer),

        __repr__     = appmethod('__repr__'),
        count        = appmethod('count'),
        index        = appmethod('index'),
        remove       = appmethod('remove'),
        reverse      = appmethod('reverse'),

        __eq__       = appmethod('__eq__'),
        __ne__       = appmethod('__ne__'),
        __lt__       = appmethod('__lt__'),
        __gt__       = appmethod('__gt__'),
        __le__       = appmethod('__le__'),
        __ge__       = appmethod('__ge__'),
        
        _isarray     = interp2app(W_Array.descr_isarray),
        __reduce__   = interp2app(W_Array.descr_reduce),
        
        
        # TODO:
        # __cmp__
        #byteswap     =
        #buffer_info  =
        #__copy__     =
        #__reduce__   =
        # insert, pop, 
    )

    mytype.w_class = W_Array

for mytype in types.values():
    make_array(mytype)

initiate=app.interphook('initiate')
def array(space, typecode, w_initializer=None):
    if len(typecode) != 1:
        msg = 'array() argument 1 must be char, not str'
        raise OperationError(space.w_TypeError, space.wrap(msg))
    typecode=typecode[0]
    
    for tc in unroll_typecodes:
        if typecode == tc:
            a = types[tc].w_class(space)
            initiate(space, a, w_initializer)
            ## if w_initializer is not None:
            ##     if not space.is_w(w_initializer, space.w_None):
            ##         a.descr_fromsequence(w_initializer)  
            break
    else:
        msg = 'bad typecode (must be c, b, B, u, h, H, i, I, l, L, f or d)'
        raise OperationError(space.w_ValueError, space.wrap(msg))


    return a
array.unwrap_spec = (ObjSpace, str, W_Root)
