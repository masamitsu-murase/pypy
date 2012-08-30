
from pypy.module.micronumpy.arrayimpl import base
from pypy.module.micronumpy import support

class ConcreteArrayIterator(base.BaseArrayIterator):
    def __init__(self, array, dtype):
        self.array = array
        self.offset = 0
        self.dtype = dtype
        self.element_size = dtype.get_size()

    def setitem(self, elem):
        self.dtype.setitem(self.array.storage, self.offset, elem)

    def next(self):
        self.offset += self.element_size

def calc_strides(shape, dtype, order):
    strides = []
    backstrides = []
    s = 1
    shape_rev = shape[:]
    if order == 'C':
        shape_rev.reverse()
    for sh in shape_rev:
        strides.append(s * dtype.get_size())
        backstrides.append(s * (sh - 1) * dtype.get_size())
        s *= sh
    if order == 'C':
        strides.reverse()
        backstrides.reverse()
    return strides, backstrides

class ConcreteArray(base.BaseArrayImplementation):
    def __init__(self, shape, dtype, order):
        self.shape = shape
        self.size = support.product(shape) * dtype.get_size()
        self.storage = dtype.itemtype.malloc(self.size)
        self.strides, self.backstrides = calc_strides(shape, dtype, order)
        self.order = order

    def get_shape(self):
        return self.shape

    def create_iter(self, dtype):
        return ConcreteArrayIterator(self, dtype)
