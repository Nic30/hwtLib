from collections import deque

from hwtLib.abstract.sim_ram import SimRam
from pyMathBitPrecise.bit_utils import mask, ValidityError
from hwtSimApi.triggers import WaitWriteOnly


class AxiDpSimRam(SimRam):
    """
    Dense RAM for simulation purposes with axi datapump interfaces

    :ivar ~.data: memory dict
    """

    def __init__(self, cellWidth, clk, rDatapumpIntf=None,
                 wDatapumpIntf=None, parent=None):
        """
        :param cellWidth: width of items in memmory
        :param clk: clk signal for synchronization
        :param parent: parent instance of SimRam
                       (memory will be shared with this instance)
        """
        assert cellWidth % 8 == 0
        super(AxiDpSimRam, self).__init__(cellWidth // 8, parent=parent)
        self.allMask = mask(self.cellSize)

        assert rDatapumpIntf is not None or wDatapumpIntf is not None, \
            "At least read or write interface has to be present"

        if rDatapumpIntf is None:
            arAg = rAg = None
        else:
            arAg = rDatapumpIntf.req._ag
            rAg = rDatapumpIntf.r._ag

        self.arAg = arAg
        self.rAg = rAg
        self.rPending = deque()

        if wDatapumpIntf is None:
            awAg = wAg = wAckAg = None
        else:
            awAg = wDatapumpIntf.req._ag
            wAg = wDatapumpIntf.w._ag
            wAckAg = wDatapumpIntf.ack._ag

        self.w_use_strb = wDatapumpIntf is not None and hasattr(
            wDatapumpIntf.w, "strb")
        self.r_use_strb = rDatapumpIntf is not None and hasattr(
            rDatapumpIntf.r, "strb")

        self.awAg = awAg
        self.wAg = wAg
        self.wAckAg = wAckAg
        self.wPending = deque()
        self.clk = clk
        if awAg is not None:
            intf = awAg.intf
        elif arAg is not None:
            intf = arAg.intf
        else:
            raise AssertionError("Need at least some interface")
        self.ID_WIDTH = intf.ID_WIDTH
        self.MAX_LEN = intf.MAX_LEN

        self._registerOnClock()

    def _registerOnClock(self):
        self.clk._sigInside.wait(self.checkRequests())

    def checkRequests(self):
        """
        Check if any request has appeared on interfaces
        """
        yield WaitWriteOnly()
        if self.arAg is not None:
            if self.arAg.data:
                self.onReadReq()

            if self.rPending:
                self.doRead()

        if self.awAg is not None:
            if self.awAg.data:
                self.onWriteReq()

            if self.wPending and self.wPending[0][2] <= len(self.wAg.data):
                self.doWrite()
        self._registerOnClock()

    def parseReq(self, req):
        for i, v in enumerate(req):
            assert v._is_full_valid(), (i, v)
        if self.MAX_LEN:
            if self.ID_WIDTH:
                assert len(req) == 4, req
                _id = req[0].val
                addr = req[1].val
                size = req[2].val + 1
                lastWordBytes = req[3].val
            else:
                assert len(req) == 3, req
                _id = 0
                addr = req[0].val
                size = req[1].val + 1
                lastWordBytes = req[2].val

        else:
            if self.ID_WIDTH:
                assert len(req) == 3, req
                _id = req[0].val
                addr = req[1].val
                size = 1
                lastWordBytes = req[2].val
            else:
                assert len(req) == 2, req
                _id = 0
                addr = req[0].val
                size = 1
                lastWordBytes = req[1].val

        if lastWordBytes == 0:
            lastWordBitmask = self.allMask
        else:
            lastWordBitmask = mask(lastWordBytes)

        return (_id, addr, size, lastWordBitmask)

    def onReadReq(self):
        readReq = self.arAg.data.pop()
        self.rPending.append(self.parseReq(readReq))

    def onWriteReq(self):
        writeReq = self.awAg.data.pop()
        self.wPending.append(self.parseReq(writeReq))

    def doRead(self):
        _id, addr, size, lastWordBitmask = self.rPending.popleft()
        HAS_ID = self.rAg.intf.ID_WIDTH > 0
        baseIndex = addr // self.cellSize
        if baseIndex * self.cellSize != addr:
            raise NotImplementedError(
                f"unaligned transaction not implemented (0x{addr:x})")

        for i in range(size):
            isLast = i == size - 1
            try:
                data = self.data[baseIndex + i]
            except KeyError:
                data = None

            if data is None:
                raise AssertionError(
                    "Invalid read of uninitialized value on addr 0x%x" %
                    (addr + i * self.cellSize))

            if self.r_use_strb:
                if isLast:
                    strb = lastWordBitmask
                else:
                    strb = self.allMask
                if HAS_ID:
                    read_trans = (_id, data, strb, isLast)
                else:
                    read_trans = (data, strb, isLast)
            else:
                if HAS_ID:
                    read_trans = (_id, data, isLast)
                else:
                    read_trans = (data, isLast)

            self.rAg.data.append(read_trans)

    def doWriteAck(self, _id):
        self.wAckAg.data.append(_id)

    def doWrite(self):
        _id, addr, size, lastWordBitmask = self.wPending.popleft()

        baseIndex = addr // self.cellSize
        if baseIndex * self.cellSize != addr:
            raise NotImplementedError("unaligned transaction not implemented")
        for i in range(size):
            if self.w_use_strb:
                data, strb, last = self.wAg.data.popleft()
                # assert data._is_full_valid()
                assert strb._is_full_valid()
                strb = strb.val
            else:
                data, last = self.wAg.data.popleft()
            try:
                data = int(data)
            except ValidityError:
                data = None
            last = bool(last)

            isLast = i == size - 1

            assert last == isLast, \
                f"write 0x{addr:x}, size {size:d}, expected last:{isLast:d} in word {i:d}"

            # if data is None:
            #     raise AssertionError(
            #         "Invalid write of uninitialized value on addr 0x%x" %
            #         (addr + i * self.cellSize))

            if isLast:
                expectedStrb = lastWordBitmask
            else:
                expectedStrb = self.allMask

            if expectedStrb != self.allMask:
                raise NotImplementedError()

            if self.w_use_strb:
                assert strb == expectedStrb

            self.data[baseIndex + i] = data

        self.doWriteAck(_id)
