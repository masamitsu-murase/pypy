from rpython.rlib.rvmprof.rvmprof import cintf
from rpython.jit.metainterp import resoperation as resoperations
import struct

class JitLogMarshall(object):
    def encode(self, op):
        str_args = [arg.repr_short(arg._repr_memo) for arg in op.getarglist()]
        descr = op.getdescr()
        line = struct.pack('<i', op.getopnum()) + ','.join(str_args)
        if descr:
            line += "|" + str(descr)
            return VMProfJitLogger.MARK_RESOP_DESCR, line
        else:
            return VMProfJitLogger.MARK_RESOP, line

    def decode(self, data):
        opnum = struct.unpack('<i', data[:4])
        # TODO

class VMProfJitLogger(JitLogMarshall):

    MARK_TRACED = 0x10

    MARK_INPUT_ARGS = 0x12

    MARK_RESOP_META = 0x13
    MARK_RESOP = 0x14
    MARK_RESOP_DESCR = 0x15
    MARK_ASM_ADDR = 0x16
    MARK_ASM = 0x17

    # the ones as parameter to log_trace
    MARK_TRACE_ASM = 0x18

    def __init__(self):
        self.cintf = cintf.setup()

    def setup_once(self):
        self.cintf.jitlog_try_init_using_env()
        if self.cintf.jitlog_filter(0x0):
            return
        count = len(resoperations.opname)
        mark = VMProfJitLogger.MARK_RESOP_META
        for opnum, opname in resoperations.opname.items():
            line = struct.pack("<h", opnum) + opname.lower()
            self.write_marked(mark, line)

    def teardown(self):
        self.cintf.jitlog_teardown()

    def write_marked(self, mark, line):
        self.cintf.jitlog_write_marked(mark, line, len(line))

    def log_trace(self, tag, args, ops,
                  faildescr=None, ops_offset={}, mc=None):
        # this is a mixture of binary and text!
        if self.cintf.jitlog_filter(tag):
            return
        assert isinstance(tag, int)

        # write the initial tag
        if faildescr is None:
            self.write_marked(tag, 'loop')
        else:
            self.write_marked(tag, 'bridge')

        # input args
        str_args = [arg.repr_short(arg._repr_memo) for arg in args]
        self.write_marked(self.MARK_INPUT_ARGS, ','.join(str_args))

        # assembler address (to not duplicate it in write_code_dump)
        if mc is not None:
            lendian_addr = struct.pack('<l', mc.absolute_addr())
            self.write_marked(self.MARK_ASM_ADDR, lendian_addr)

        for i,op in enumerate(ops):
            mark, line = self.encode(op)
            self.write_marked(mark, line)
            self.write_core_dump(ops, i, op, ops_offset, mc)

    def write_core_dump(self, operations, i, op, ops_offset, mc):
        if mc is None:
            return

        op2 = None
        j = i+1
        # find the next op that is in the offset hash
        while j < len(operations):
            op2 = operations[j]
            if op in ops_offset:
                break
            j += 1

        # this op has no known offset in the machine code (it might be
        # a debug operation)
        if op not in ops_offset:
            return
        # there is no well defined boundary for the end of the
        # next op in the assembler
        if op2 is not None and op2 not in ops_offset:
            return
        dump = []

        start_offset = ops_offset[op]
        # end offset is either the last pos in the assembler
        # or the offset of op2
        if op2 is None:
            end_offset = mc.get_relative_pos()
        else:
            end_offset = ops_offset[op2]

        dump = mc.copy_core_dump(mc.absolute_addr(), start_offset)
        self.write_marked(self.MARK_ASM, dump)


