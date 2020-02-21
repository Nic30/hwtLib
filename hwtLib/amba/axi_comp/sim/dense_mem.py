from collections import deque

from hwt.hdl.types.bits import Bits
from hwt.hdl.value import Value
from hwtLib.abstract.denseMemory import DenseMemory
from hwtLib.amba.constants import RESP_OKAY
from pyMathBitPrecise.bit_utils import mask, setBitRange, selectBit,\
    selectBitRange


class Axi3DenseMem(DenseMemory):
    """
    Simulation memory for Axi3/4 interfaces (slave component)
    """

    def __init__(self, clk, axi=None, axiAR=None, axiR=None, axiAW=None,
                 axiW=None, axiB=None, parent=None):
        """
        :param clk: clk which should this memory use in simulation
        :param axi: axi (Axi3/4 master) interface to listen on
        :param axiAR, axiR, axiAW, axiW, axiB: splited interface use this
            if you do not have full axi interface
        :attention: use axi or axi parts not bouth
        :param parent: parent instance of this memory, memory will operate
            with same memory as parent one
        :attention: memories are commiting into memory in "data" property
            after transaction is complete
        """
        self.parent = parent
        if parent is None:
            self.data = {}
        else:
            self.data = parent.data

        if axi is not None:
            assert axiAR is None
            assert axiR is None
            self.arAg = axi._ag.ar
            self.rAg = axi._ag.r
            DW = int(axi.DATA_WIDTH)
            self.awAg = axi._ag.aw
            self.wAg = axi._ag.w
            self.wAckAg = axi._ag.b
        else:
            assert axi is None
            if axiAR is not None:
                self.arAg = axiAR._ag
                self.rAg = axiR._ag
                DW = int(axiR.DATA_WIDTH)
            else:
                assert axiR is None
                self.arAg = None
                self.rAg = None

            if axiAW is not None:
                self.awAg = axiAW._ag
                self.wAg = axiW._ag
                self.wAckAg = axiB._ag
                DW = int(axiW.DATA_WIDTH)
            else:
                assert axiW is None
                assert axiB is None
                self.awAg = None
                self.wAg = None
                self.wAckAg = None

            assert axiAR is not None or axiAW is not None

        if self.wAg is not None:
            self.HAS_W_ID = hasattr(self.wAg.intf, "id")
        else:
            self.HAS_W_ID = False

        self.cellSize = DW // 8
        self.allMask = mask(self.cellSize)
        self.word_t = Bits(self.cellSize * 8)

        self.rPending = deque()
        self.wPending = deque()
        self.clk = clk
        self._registerOnClock()

    def parseReq(self, req):
        try:
            req = [int(v) for v in req]
        except ValueError:
            raise AssertionError("Invalid AXI request", req) from None

        _id = req[0]
        addr = req[1]
        size = req[4] + 1

        return (_id, addr, size, self.allMask)

    def add_r_ag_data(self, _id, data, isLast):
        self.rAg.data.append((_id, data, RESP_OKAY, isLast))

    def doRead(self):
        _id, addr, size, _ = self.rPending.popleft()

        baseIndex = addr // self.cellSize
        if baseIndex * self.cellSize != addr:
            offset = addr % self.cellSize
            word_t = self.word_t
            word_mask0 = mask(8 * self.cellSize)
            word_mask1 = mask((self.cellSize - offset) * 8)
        else:
            offset = 0

        mem = self.data
        for i in range(size):
            isLast = i == size - 1
            data = mem.get(baseIndex + i, None)
            if offset != 0:
                data1 = mem.get(baseIndex + i + 1, None)
                if data is None:
                    if data1 is None:
                        # data = None
                        pass
                    else:
                        data = data1 << ((self.cellSize - offset) * 8)
                        data = data & word_mask1
                else:
                    if data1 is None:
                        if isinstance(data, int):
                            data = word_t.from_py(
                                data >> (offset * 8),
                                word_mask0)
                    else:
                        data = ((data >> (offset * 8)) & word_mask0) \
                            | ((data1 << ((self.cellSize - offset) * 8)) & word_mask1)

            if data is None:
                raise AssertionError(
                    "Invalid read of uninitialized value on addr 0x%x"
                    % (addr + i * self.cellSize))

            self.add_r_ag_data(_id, data, isLast)

    def pop_w_ag_data(self, _id):
        if self.HAS_W_ID:
            _id2, data, strb, last = self.wAg.data.popleft()
            _id2 = int(_id2)
            assert _id == _id2
        else:
            data, strb, last = self.wAg.data.popleft()
        return (data, strb, last)

    def _write_single_word(self, data: Value, strb: int, word_i: int):
        if strb == 0:
            return
        if strb != self.allMask:
            cur = self.data.get(word_i, None)
            if cur is None:
                cur_val = 0
                cur_mask = 0
            elif isinstance(cur, int):
                cur_val = cur
                cur_mask = self.allMask
            else:
                cur_val = cur.val
                cur_mask = cur.vld_mask

            for i in range(self.cellSize):
                if selectBit(strb, i):
                    cur_val = setBitRange(
                        cur_val, i * 8, 8, selectBitRange(data.val, i * 8, 8))
                    cur_mask = setBitRange(
                        cur_mask, i * 8, 8, selectBitRange(data.vld_mask, i * 8, 8))
            if cur_mask == self.allMask:
                data = cur_val
            else:
                data = self.word_t.from_py(cur_val, cur_mask)
        # print("data[%d] = %r" % (word_i, data))
        self.data[word_i] = data

    def doWrite(self):
        _id, addr, size, _ = self.wPending.popleft()

        baseIndex = addr // self.cellSize
        offset = addr % self.cellSize
        for i in range(size):
            data, strb, last = self.pop_w_ag_data(_id)
            strb = int(strb)
            last = int(last)
            last = bool(last)
            isLast = i == size - 1
            assert last == isLast, (addr, size, i)
            if offset == 0:
                # print("alig", data, strb)
                self._write_single_word(data, strb, baseIndex + i)
            else:
                # print("init", data, strb)
                d0 = data << (offset * 8)
                strb0 = strb << offset
                d1 = (data >> (offset * 8)) & self.allMask
                strb1 = (strb >> offset) & mask(self.cellSize)
                # print("split", d0, d1, strb0, strb1)
                self._write_single_word(d0, strb0, baseIndex + i)
                self._write_single_word(d1, strb1, baseIndex + i + 1)
        self.doWriteAck(_id)

    def doWriteAck(self, _id):
        self.wAckAg.data.append((_id, RESP_OKAY))
