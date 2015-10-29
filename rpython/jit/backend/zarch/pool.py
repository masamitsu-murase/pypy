from rpython.jit.backend.zarch import registers as r
from rpython.jit.backend.zarch import locations as l
from rpython.jit.metainterp.history import (INT, REF, FLOAT,
        TargetToken)
from rpython.rtyper.lltypesystem import lltype, rffi, llmemory

class LiteralPool(object):
    def __init__(self):
        self.size = 0
        # the offset to index the pool
        self.pool_start = 0
        self.offset_map = {}

    def ensure_can_hold_constants(self, op):
        if op.is_guard():
            # 1x gcmap pointer
            # 1x target address
            self.offset_map[op.getdescr()] = self.size
            self.reserve_literal(2 * 8)
        for arg in op.getarglist():
            if arg.is_constant():
                self.offset_map[arg] = self.size
                self.reserve_literal(8)

    def reserve_literal(self, size):
        self.size += size

    def reset(self):
        self.size = 0
        self.rel_offset = 0

    def walk_operations(self, operations):
        # O(len(operations)). I do not think there is a way
        # around this.
        #
        # Problem:
        # constants such as floating point operations, plain pointers,
        # or integers might serve as parameter to an operation. thus
        # it must be loaded into a register. You cannot do this with
        # assembler immediates, because the biggest immediate value
        # is 32 bit for branch instructions.
        #
        # Solution:
        # the current solution (gcc does the same), use a literal pool
        # located at register r13. This one can easily offset with 20
        # bit signed values (should be enough)
        for op in operations:
            self.ensure_can_hold_constants(op)

    def pre_assemble(self, mc, operations):
        self.reset()
        self.walk_operations(operations)
        if self.size == 0:
            # no pool needed!
            return
        if self.size % 2 == 1:
            self.size += 1
        assert self.size < 2**16-1
        mc.BRAS(r.POOL, l.imm(self.size+mc.BRAS._byte_count))
        self.pool_offset = mc.get_relative_pos()
        mc.write('\x00' * self.size)
        print "pool with %d bytes %d // 8" % (self.size, self.size // 8)

    def overwrite_64(self, mc, index, value):
        print("value", hex(value), "at", index)
        mc.overwrite(index,   chr(value >> 56 & 0xff))
        mc.overwrite(index+1, chr(value >> 48 & 0xff))
        mc.overwrite(index+2, chr(value >> 40 & 0xff))
        mc.overwrite(index+3, chr(value >> 32 & 0xff))
        mc.overwrite(index+4, chr(value >> 24 & 0xff))
        mc.overwrite(index+5, chr(value >> 16 & 0xff))
        mc.overwrite(index+6, chr(value >> 8 & 0xff))
        mc.overwrite(index+7, chr(value & 0xff))

    def post_assemble(self, mc, pending_guard_tokens):
        if self.size == 0:
            return
        for val, offset in self.offset_map.items():
            if val.is_constant():
                if val.type == FLOAT:
                    self.overwrite_64(mc, offset, float2longlong(val.value))
                elif val.type == INT:
                    self.overwrite_64(mc, offset, val.value)
                else:
                    raise NotImplementedError
            else:
                pass

        for guard_token in pending_guard_tokens:
            descr = guard_token.faildescr
            offset = self.offset_map[descr]
            guard_token._pool_offset = offset
            ptr = rffi.cast(lltype.Signed, guard_token.gcmap)
            self.overwrite_64(mc, offset + 8, ptr)
        self.offset_map.clear()

