from collections import deque

from hwt.hdl.types.bits import Bits
from hwt.hdl.value import HValue
from hwtLib.abstract.sim_ram import SimRam
from hwtLib.avalon.mm import AvalonMM, RESP_OKAY
from hwtSimApi.triggers import WaitWriteOnly
from pyMathBitPrecise.bit_utils import mask, set_bit_range, get_bit, \
    get_bit_range
from hwt.hdl.constants import READ, READ_WRITE, WRITE


class AvalonMmSimRam(SimRam):
    """
    Simulation memory for AvalonMM interfaces (slave component)
    """

    def __init__(self, avalon_mm: AvalonMM, parent=None, clk=None, allow_unaligned_addr=False):
        """
        :param clk: clk which should this memory use in simulation
            (if None the clk associated with an interface is used)
        :param avalon_mm: avalon_mm (AvalonMM master) interface to listen on
        :param parent: parent instance of this memory, memory will operate
            with same memory as parent one
        :attention: memories are commiting into memory in "data" property
            after transaction is complete
        """

        DW = avalon_mm.DATA_WIDTH
        self.allow_unaligned_addr = allow_unaligned_addr
        SimRam.__init__(self, DW // 8, parent=parent)

        self.allMask = mask(self.cellSize)
        self.word_t = Bits(self.cellSize * 8)

        if clk is None:
            clk = avalon_mm._getAssociatedClk()
        self.bus = avalon_mm
        self.clk = clk
        self._registerOnClock()

    def _registerOnClock(self):
        self.clk._sigInside.wait(self.checkRequests())

    def checkRequests(self):
        """
        Check if any request has appeared on interfaces
        """
        yield WaitWriteOnly()
        req = self.bus._ag.addrAg.data
        if req:
            rw, addr, burstCount, d, be = self.parseReq(req[0])
            if rw in (WRITE, READ_WRITE):
                if burstCount <= len(req):
                    req.popleft()
                    data_words = [(d, be)]
                    if burstCount > 1:
                        for _ in range(burstCount - 1):
                            _rw, _addr, _burstCount, d, be = self.parseReq(req.popleft())
                            assert (rw, addr, burstCount) == (_rw, _addr, _burstCount), (
                                "Must stay stable until end of burst", (rw, addr, burstCount), (_rw, _addr, _burstCount))
                            # consume the additional write requests which were generated during write data send
                            data_words.append((d, be))

                    if rw == READ_WRITE:
                        self.doRead(addr, burstCount)

                    self.doWrite(addr, data_words)

            elif rw == READ:
                req.popleft()
                self.doRead(addr, burstCount)
            else:
                raise AssertionError("Unknown request", req[0])

        self._registerOnClock()

    def parseReq(self, req):
        rw, addr, burstCount, d, be = req
        try:
            addr = int(addr)
        except ValueError:
            raise AssertionError("Invalid AvalonMM request", req) from None
        try:
            burstCount = int(burstCount)
        except ValueError:
            raise AssertionError("Invalid AvalonMM request", req) from None

        return (rw, addr, burstCount, d, be)

    def doRead(self, addr, size):
        baseIndex = addr // self.cellSize
        if baseIndex * self.cellSize != addr:
            if not self.allow_unaligned_addr:
                raise ValueError("not aligned", addr)
            offset = addr % self.cellSize
            word_t = self.word_t
            word_mask0 = mask(8 * self.cellSize)
            word_mask1 = mask((self.cellSize - offset) * 8)
        else:
            offset = 0

        mem = self.data
        for i in range(size):
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

            self.add_r_ag_data(data)

    def add_r_ag_data(self, data):
        self.bus._ag.rDataAg.data.append((data, RESP_OKAY))

    def _write_single_word(self, data: HValue, strb: int, word_i: int):
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
                if get_bit(strb, i):
                    cur_val = set_bit_range(
                        cur_val, i * 8, 8, get_bit_range(data.val, i * 8, 8))
                    cur_mask = set_bit_range(
                        cur_mask, i * 8, 8, get_bit_range(data.vld_mask, i * 8, 8))
            if cur_mask == self.allMask:
                data = cur_val
            else:
                data = self.word_t.from_py(cur_val, cur_mask)
        # print(f"data[{word_i:d}] = {data}")
        self.data[word_i] = data

    def doWrite(self, addr, data_words):
        baseIndex = addr // self.cellSize
        offset = addr % self.cellSize
        if offset and not self.allow_unaligned_addr:
            raise ValueError("not aligned", addr)
        for i, (data, strb) in enumerate(data_words):
            strb = int(strb)
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
        self.doWriteAck()

    def doWriteAck(self):
        self.bus._ag.wRespAg.data.append(RESP_OKAY)

