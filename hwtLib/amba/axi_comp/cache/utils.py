from hwt.math import log2ceil
from hwt.pyUtils.typingFuture import override
from hwtLib.commonHwIO.addr_data import HwIOAddrData
from hwtLib.mem.cam import CamMultiPort


class CamWithReadPort(CamMultiPort):
    """
    Content addressable memory with a read port which can be used
    to read cam array by index

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        CamMultiPort.hwConfig(self)
        self.USE_VLD_BIT = False

    @override
    def hwDeclr(self):
        assert not self.USE_VLD_BIT
        CamMultiPort.hwDeclr(self)
        r = self.read = HwIOAddrData()
        r.ADDR_WIDTH = log2ceil(self.ITEMS - 1)
        r.DATA_WIDTH = self.KEY_WIDTH

    @override
    def hwImpl(self):
        CamMultiPort.hwImpl(self)
        self.read.data(self._mem[self.read.addr])

