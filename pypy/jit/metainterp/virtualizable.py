from pypy.rpython.lltypesystem import lltype, llmemory
from pypy.rpython.ootypesystem import ootype
from pypy.rpython.annlowlevel import cast_base_ptr_to_instance
from pypy.rpython.rclass import IR_IMMUTABLE_ARRAY, IR_IMMUTABLE
from pypy.rpython import rvirtualizable2
from pypy.rlib.objectmodel import we_are_translated
from pypy.rlib.unroll import unrolling_iterable
from pypy.rlib.nonconst import NonConstant
from pypy.jit.metainterp.typesystem import deref, fieldType, arrayItem
from pypy.jit.metainterp import history, jitframe
from pypy.jit.metainterp.warmstate import wrap, unwrap
from pypy.rlib.objectmodel import specialize

class VirtualizableInfo(object):

    def __init__(self, warmrunnerdesc, VTYPEPTR):
        self.warmrunnerdesc = warmrunnerdesc
        cpu = warmrunnerdesc.cpu
        self.TOKEN_TRACING_RESCALL = cpu.TOKEN_TRACING_RESCALL
        if cpu.ts.name == 'ootype':
            import py
            py.test.skip("ootype: fix virtualizables")
        self.cpu = cpu
        self.BoxArray = cpu.ts.BoxRef
        #
        while 'virtualizable2_accessor' not in deref(VTYPEPTR)._hints:
            VTYPEPTR = cpu.ts.get_superclass(VTYPEPTR)
        self.VTYPEPTR = VTYPEPTR
        self.VTYPE = VTYPE = deref(VTYPEPTR)
        self.jit_frame_descr = cpu.fielddescrof(VTYPE, 'jit_frame')
        #
        accessor = VTYPE._hints['virtualizable2_accessor']
        all_fields = accessor.fields
        static_fields = []
        array_fields = []
        for name, tp in all_fields.iteritems():
            if tp == IR_IMMUTABLE_ARRAY:
                array_fields.append(name)
            elif tp == IR_IMMUTABLE:
                static_fields.append(name)
            else:
                raise Exception("unknown type: %s" % tp)
        self.static_fields = static_fields
        self.array_fields = array_fields
        #
        FIELDTYPES = [fieldType(VTYPE, name) for name in static_fields]
        ARRAYITEMTYPES = []
        for name in array_fields:
            ARRAYPTR = fieldType(VTYPE, name)
            ARRAY = deref(ARRAYPTR)
            assert isinstance(ARRAYPTR, (lltype.Ptr, ootype.Array))
            assert isinstance(ARRAY, (lltype.GcArray, ootype.Array))
            ARRAYITEMTYPES.append(arrayItem(ARRAY))
        self.array_descrs = [cpu.arraydescrof(deref(fieldType(VTYPE, name)))
                             for name in array_fields]
        #
        self.num_static_extra_boxes = len(static_fields)
        self.num_arrays = len(array_fields)
        self.static_field_to_extra_box = dict(
            [(name, i) for (i, name) in enumerate(static_fields)])
        self.array_field_counter = dict(
            [(name, i) for (i, name) in enumerate(array_fields)])
        self.static_extra_types = [history.getkind(TYPE)
                                   for TYPE in FIELDTYPES]
        self.arrayitem_extra_types = [history.getkind(ITEM)
                                      for ITEM in ARRAYITEMTYPES]
        self.static_field_descrs = [cpu.fielddescrof(VTYPE, name)
                                    for name in static_fields]
        self.array_field_descrs = [cpu.fielddescrof(VTYPE, name)
                                   for name in array_fields]
        self.static_field_by_descrs = dict(
            [(descr, i) for (i, descr) in enumerate(self.static_field_descrs)])
        self.array_field_by_descrs = dict(
            [(descr, i) for (i, descr) in enumerate(self.array_field_descrs)])
        #
        getlength = cpu.ts.getlength
        getarrayitem = cpu.ts.getarrayitem
        setarrayitem = cpu.ts.setarrayitem
        #
        def read_boxes(cpu, virtualizable):
            assert lltype.typeOf(virtualizable) == llmemory.GCREF
            virtualizable = cast_gcref_to_vtype(virtualizable)
            boxes = []
            for _, fieldname in unroll_static_fields:
                x = getattr(virtualizable, fieldname)
                boxes.append(wrap(cpu, x))
            for _, fieldname in unroll_array_fields:
                lst = getattr(virtualizable, fieldname)
                for i in range(getlength(lst)):
                    boxes.append(wrap(cpu, getarrayitem(lst, i)))
            return boxes
        #
        def write_boxes(virtualizable, boxes):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            i = 0
            for FIELDTYPE, fieldname in unroll_static_fields:
                x = unwrap(FIELDTYPE, boxes[i])
                setattr(virtualizable, fieldname, x)
                i = i + 1
            for ARRAYITEMTYPE, fieldname in unroll_array_fields:
                lst = getattr(virtualizable, fieldname)
                for j in range(getlength(lst)):
                    x = unwrap(ARRAYITEMTYPE, boxes[i])
                    setarrayitem(lst, j, x)
                    i = i + 1
            assert len(boxes) == i + 1
        #
        def write_from_resume_data_partial(virtualizable, reader, numb):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            # Load values from the reader (see resume.py) described by
            # the list of numbers 'nums', and write them in their proper
            # place in the 'virtualizable'.  This works from the end of
            # the list and returns the index in 'nums' of the start of
            # the virtualizable data found, allowing the caller to do
            # further processing with the start of the list.
            i = len(numb.nums) - 1
            assert i >= 0
            for ARRAYITEMTYPE, fieldname in unroll_array_fields_rev:
                lst = getattr(virtualizable, fieldname)
                for j in range(getlength(lst)-1, -1, -1):
                    i -= 1
                    assert i >= 0
                    x = reader.load_value_of_type(ARRAYITEMTYPE, numb.nums[i])
                    setarrayitem(lst, j, x)
            for FIELDTYPE, fieldname in unroll_static_fields_rev:
                i -= 1
                assert i >= 0
                x = reader.load_value_of_type(FIELDTYPE, numb.nums[i])
                setattr(virtualizable, fieldname, x)
            return i
        #
        def load_list_of_boxes(virtualizable, reader, numb):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            # Uses 'virtualizable' only to know the length of the arrays;
            # does not write anything into it.  The returned list is in
            # the format expected of virtualizable_boxes, so it ends in
            # the virtualizable itself.
            i = len(numb.nums) - 1
            assert i >= 0
            boxes = [reader.decode_box_of_type(self.VTYPEPTR, numb.nums[i])]
            for ARRAYITEMTYPE, fieldname in unroll_array_fields_rev:
                lst = getattr(virtualizable, fieldname)
                for j in range(getlength(lst)-1, -1, -1):
                    i -= 1
                    assert i >= 0
                    box = reader.decode_box_of_type(ARRAYITEMTYPE,numb.nums[i])
                    boxes.append(box)
            for FIELDTYPE, fieldname in unroll_static_fields_rev:
                i -= 1
                assert i >= 0
                box = reader.decode_box_of_type(FIELDTYPE, numb.nums[i])
                boxes.append(box)
            boxes.reverse()
            return boxes
        #
        def check_boxes(virtualizable, boxes):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            # for debugging
            i = 0
            for FIELDTYPE, fieldname in unroll_static_fields:
                x = unwrap(FIELDTYPE, boxes[i])
                assert getattr(virtualizable, fieldname) == x
                i = i + 1
            for ARRAYITEMTYPE, fieldname in unroll_array_fields:
                lst = getattr(virtualizable, fieldname)
                for j in range(getlength(lst)):
                    x = unwrap(ARRAYITEMTYPE, boxes[i])
                    assert getarrayitem(lst, j) == x
                    i = i + 1
            assert len(boxes) == i + 1
        #
        def get_index_in_array(virtualizable, arrayindex, index):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            index += self.num_static_extra_boxes
            j = 0
            for _, fieldname in unroll_array_fields:
                if arrayindex == j:
                    return index
                lst = getattr(virtualizable, fieldname)
                index += getlength(lst)
                j = j + 1
            assert False, "invalid arrayindex"
        #
        def get_array_length(virtualizable, arrayindex):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            j = 0
            for _, fieldname in unroll_array_fields:
                if arrayindex == j:
                    lst = getattr(virtualizable, fieldname)
                    return getlength(lst)
                j = j + 1
            assert False, "invalid arrayindex"
        #
        unroll_static_fields = unrolling_iterable(zip(FIELDTYPES,
                                                      static_fields))
        unroll_array_fields = unrolling_iterable(zip(ARRAYITEMTYPES,
                                                     array_fields))
        unroll_static_fields_rev = unrolling_iterable(
                                          reversed(list(unroll_static_fields)))
        unroll_array_fields_rev  = unrolling_iterable(
                                          reversed(list(unroll_array_fields)))
        self.read_boxes = read_boxes
        self.write_boxes = write_boxes
        self.write_from_resume_data_partial = write_from_resume_data_partial
        self.load_list_of_boxes = load_list_of_boxes
        self.check_boxes = check_boxes
        self.get_index_in_array = get_index_in_array
        self.get_array_length = get_array_length

        def cast_to_vtype(virtualizable):
            return self.cpu.ts.cast_to_instance_maybe(VTYPEPTR, virtualizable)
        self.cast_to_vtype = cast_to_vtype

        def cast_gcref_to_vtype(virtualizable):
            assert lltype.typeOf(virtualizable) == llmemory.GCREF
            return lltype.cast_opaque_ptr(VTYPEPTR, virtualizable)
        self.cast_gcref_to_vtype = cast_gcref_to_vtype

        def reset_jit_frame(virtualizable):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            virtualizable.jit_frame = jitframe.TOKEN_NONE
        self.reset_jit_frame = reset_jit_frame

        def clear_jit_frame(virtualizable):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            if virtualizable.jit_frame != jitframe.TOKEN_NONE:
                force_now(virtualizable)
                assert virtualizable.jit_frame == jitframe.TOKEN_NONE
        self.clear_jit_frame = clear_jit_frame

        def tracing_before_residual_call(virtualizable):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            assert virtualizable.jit_frame == jitframe.TOKEN_NONE
            virtualizable.jit_frame = self.TOKEN_TRACING_RESCALL
        self.tracing_before_residual_call = tracing_before_residual_call

        def tracing_after_residual_call(virtualizable):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            if virtualizable.jit_frame != jitframe.TOKEN_NONE:
                # not modified by the residual call; assert that it is still
                # set to TOKEN_TRACING_RESCALL and clear it.
                assert virtualizable.jit_frame == self.TOKEN_TRACING_RESCALL
                virtualizable.jit_frame = jitframe.TOKEN_NONE
                return False
            else:
                # marker "modified during residual call" set.
                return True
        self.tracing_after_residual_call = tracing_after_residual_call

        def force_now(virtualizable):
            token = virtualizable.jit_frame
            if token == self.TOKEN_TRACING_RESCALL:
                # The values in the virtualizable are always correct during
                # tracing.  We only need to reset jit_frame to TOKEN_NONE
                # as a marker for the tracing, to tell it that this
                # virtualizable escapes.
                virtualizable.jit_frame = jitframe.TOKEN_NONE
            else:
                from pypy.jit.metainterp.compile import ResumeGuardForcedDescr
                ResumeGuardForcedDescr.force_now(cpu, token)
                assert virtualizable.jit_frame == jitframe.TOKEN_NONE
        force_now._dont_inline_ = True
        self.force_now = force_now

        def is_token_nonnull_gcref(virtualizable):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            return virtualizable.jit_frame != jitframe.TOKEN_NONE
        self.is_token_nonnull_gcref = is_token_nonnull_gcref

        def reset_token_gcref(virtualizable):
            virtualizable = cast_gcref_to_vtype(virtualizable)
            virtualizable.jit_frame = jitframe.TOKEN_NONE
        self.reset_token_gcref = reset_token_gcref

    def _freeze_(self):
        return True

    def finish(self):
        #
        def force_virtualizable_if_necessary(virtualizable):
            if virtualizable.jit_frame != jitframe.TOKEN_NONE:
                self.force_now(virtualizable)
        self.force_virtualizable_if_necessary = force_virtualizable_if_necessary
        force_virtualizable_if_necessary._always_inline_ = True
        #
        all_graphs = self.warmrunnerdesc.translator.graphs
        ts = self.warmrunnerdesc.cpu.ts
        (_, FUNCPTR) = ts.get_FuncType([self.VTYPEPTR], lltype.Void)
        funcptr = self.warmrunnerdesc.helper_func(
            FUNCPTR, force_virtualizable_if_necessary)
        rvirtualizable2.replace_force_virtualizable_with_call(
            all_graphs, self.VTYPEPTR, funcptr)

    def unwrap_virtualizable_box(self, virtualizable_box):
        return virtualizable_box.getref(llmemory.GCREF)
     
    def is_vtypeptr(self, TYPE):
        return rvirtualizable2.match_virtualizable_type(TYPE, self.VTYPEPTR)
