from hwt.hdl.constants import READ, WRITE
from hwtLib.abstract.sim_ram import SimRam
from hwtLib.cesnet.mi32.intf import Mi32
from pyMathBitPrecise.bit_utils import mask
from hwtSimApi.triggers import WaitWriteOnly


class Mi32SimRam(SimRam):

    def __init__(self, mi32: Mi32, parent=None):
        super(Mi32SimRam, self).__init__(mi32.DATA_WIDTH // 8, parent=parent)
        self.intf = mi32
        self.clk = mi32._getAssociatedClk()
        self._word_bytes = mi32.DATA_WIDTH // 8
        self._word_mask = mask(self._word_bytes)
        self._registerOnClock()

    def _registerOnClock(self):
        self.clk._sigInside.wait(self.checkRequests())

    def checkRequests(self):
        """
        Check if any request has appeared on interfaces
        """
        yield WaitWriteOnly()
        req = self.intf._ag.requests
        if req:
            self.on_req(req)

        self._registerOnClock()

    def on_read(self, addr):
        addr = int(addr)
        if addr % self._word_bytes != 0:
            raise NotImplementedError("Unaligned read")

        d = self.data[int(addr) // self._word_bytes]
        self.intf._ag.r_data.append(d)

    def on_write(self, addr, val, byteen):
        addr = int(addr)
        if addr % self._word_bytes != 0:
            raise NotImplementedError("Unaligned write", addr)

        if int(byteen) == self._word_mask:
            self.data[addr // self._word_bytes] = val
        else:
            raise NotImplementedError("Masked write")

    def on_req(self, req):
        mode, addr, val, byteen = req.popleft()
        if mode == READ:
            self.on_read(addr)
        else:
            assert mode == WRITE
            self.on_write(addr, val, byteen)
