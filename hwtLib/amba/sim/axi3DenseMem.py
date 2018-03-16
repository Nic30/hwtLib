from collections import deque

from hwt.bitmask import mask
from hwtLib.abstract.denseMemory import DenseMemory
from hwtLib.amba.constants import RESP_OKAY


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
        self.rPending = deque()

        self.wPending = deque()

        self._registerOnClock(clk)

    def parseReq(self, req):
        for i, v in enumerate(req):
            assert v._isFullVld(), ("Invalid AXI request", i, v)

        _id = req[0].val
        addr = req[1].val
        size = req[4].val + 1

        return (_id, addr, size, self.allMask)

    def doRead(self):
        _id, addr, size, lastWordBitmask = self.rPending.popleft()

        baseIndex = addr // self.cellSize
        if baseIndex * self.cellSize != addr:
            raise NotImplementedError(
                "unaligned transaction not implemented (0x%x)" % addr)

        for i in range(size):
            isLast = i == size - 1
            try:
                data = self.data[baseIndex + i]
            except KeyError:
                data = None

            if data is None:
                raise AssertionError(
                    "Invalid read of uninitialized value on addr 0x%x"
                    % (addr + i * self.cellSize))

            self.rAg.data.append((_id, data, RESP_OKAY, isLast))

    def doWrite(self):
        _id, addr, size, lastWordBitmask = self.wPending.popleft()

        baseIndex = addr // self.cellSize
        if baseIndex * self.cellSize != addr:
            raise NotImplementedError("unaligned transaction not implemented")

        for i in range(size):
            if self.HAS_W_ID:
                _id2, data, strb, last = self.wAg.data.popleft()
                assert _id2._isFullVld()
                assert _id == _id2.val
            else:
                data, strb, last = self.wAg.data.popleft()

            # assert data._isFullVld()
            assert strb._isFullVld()
            assert last._isFullVld()

            data, strb, last = data.val, strb.val, bool(last.val)

            isLast = i == size - 1

            assert last == isLast, (addr, size, i)

            if data is None:
                raise AssertionError(
                    "Invalid read of uninitialized value on addr 0x%x"
                    % (addr + i * self.cellSize))

            if isLast:
                expectedStrb = lastWordBitmask
            else:
                expectedStrb = self.allMask

            if expectedStrb != self.allMask:
                raise NotImplementedError()
            assert strb == expectedStrb

            self.data[baseIndex + i] = data

        self.doWriteAck(_id)

    def doWriteAck(self, _id):
        self.wAckAg.data.append((_id, RESP_OKAY))
