from pypy.rpython.lltypesystem import lltype, lloperation
from pypy.translator.stm.writebarrier import is_immutable
from pypy.objspace.flow.model import SpaceOperation, Constant
from pypy.translator.unsimplify import varoftype


ALWAYS_ALLOW_OPERATIONS = set([
    'direct_call', 'force_cast', 'keepalive', 'cast_ptr_to_adr',
    'debug_print', 'debug_assert', 'cast_opaque_ptr', 'hint',
    'indirect_call', 'stack_current', 'gc_stack_bottom',
    'cast_current_ptr_to_int',   # this variant of 'cast_ptr_to_int' is ok
    'jit_force_virtual', 'jit_force_virtualizable',
    'jit_force_quasi_immutable', 'jit_marker', 'jit_is_virtual',
    'jit_record_known_class',
    'gc_identityhash', 'gc_id',
    'gc_adr_of_root_stack_top',
    ])
ALWAYS_ALLOW_OPERATIONS |= set(lloperation.enum_tryfold_ops())

for opname, opdesc in lloperation.LL_OPERATIONS.iteritems():
    if opname.startswith('stm_'):
        ALWAYS_ALLOW_OPERATIONS.add(opname)

GETTERS = set(['getfield', 'getarrayitem', 'getinteriorfield'])
SETTERS = set(['setfield', 'setarrayitem', 'setinteriorfield'])
MALLOCS = set(['malloc', 'malloc_varsize',
               'malloc_nonmovable', 'malloc_nonmovable_varsize'])

# ____________________________________________________________

def should_turn_inevitable_getter_setter(op):
    # Getters and setters are allowed if their first argument is a GC pointer.
    # If it is a RAW pointer, and it is a read from a non-immutable place,
    # and it doesn't use the hint 'stm_dont_track_raw_accesses', then they
    # turn inevitable.
    S = op.args[0].concretetype.TO
    if S._gckind == 'gc':
        return False
    if is_immutable(op):
        return False
    if S._hints.get('stm_dont_track_raw_accesses', False):
        return False
    return True

def should_turn_inevitable(op):
    # Always-allowed operations never cause a 'turn inevitable'
    if op.opname in ALWAYS_ALLOW_OPERATIONS:
        return False
    #
    # Getters and setters
    if op.opname in GETTERS:
        if op.result.concretetype is lltype.Void:
            return False
        return should_turn_inevitable_getter_setter(op)
    if op.opname in SETTERS:
        if op.args[-1].concretetype is lltype.Void:
            return False
        return should_turn_inevitable_getter_setter(op)
    #
    # Mallocs
    if op.opname in MALLOCS:
        flags = op.args[1].value
        return flags['flavor'] != 'gc'
    #
    # Entirely unsupported operations cause a 'turn inevitable'
    return True


def turn_inevitable_op(info):
    c_info = Constant(info, lltype.Void)
    return SpaceOperation('stm_become_inevitable', [c_info],
                          varoftype(lltype.Void))

def insert_turn_inevitable(translator, graph):
    for block in graph.iterblocks():
        for i in range(len(block.operations)-1, -1, -1):
            op = block.operations[i]
            if should_turn_inevitable(op):
                inev_op = turn_inevitable_op(op.opname)
                block.operations.insert(i, inev_op)
