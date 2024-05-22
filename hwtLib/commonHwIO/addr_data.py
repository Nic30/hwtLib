from hwt.hwIO import HwIO
from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIOVectSignal, HwIORdVldSync, HwIOSignal
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION


class HwIOAddrData(HwIO):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.ADDR_WIDTH = HwParam(32)
        self.DATA_WIDTH = HwParam(64)

    @override
    def hwDeclr(self):
        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        self.data = HwIOVectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)


class HwIOAddrDataRdVld(HwIORdVldSync):
    """
    Simple handshaked interface with address and data signal

    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        self.ADDR_WIDTH = HwParam(8)
        self.DATA_WIDTH = HwParam(8)
        self.HAS_MASK = HwParam(False)

    @override
    def hwDeclr(self):
        super(HwIOAddrDataRdVld, self).hwDeclr()
        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        self.data = HwIOVectSignal(self.DATA_WIDTH)
        if self.HAS_MASK:
            assert self.DATA_WIDTH % 8 == 0, self.DATA_WIDTH
            self.mask = HwIOVectSignal(self.DATA_WIDTH // 8)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        if self.HAS_MASK:
            self._ag = HwIOAddrDataMaskRdVldAgent(sim, self)
        else:
            self._ag = HwIOAddrDataRdVldAgent(sim, self)


class HwIOAddrDataVldRdVld(HwIOAddrDataRdVld):
    """
    :see: :class:`.HwIOAddrDataRdVld` with a vld_flag signal

    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        super(HwIOAddrDataVldRdVld, self).hwDeclr()
        self.vld_flag = HwIOSignal()

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOAddrDataVldAgent(sim, self)


class HwIOAddrDataBitMaskRdVld(HwIOAddrDataRdVld):
    """
    :see: :class:`.HwIOAddrDataRdVld` with a mask signal
    :note: mask has 1b granularity

    .. hwt-autodoc::
    """

    @override
    def hwDeclr(self):
        super(HwIOAddrDataBitMaskRdVld, self).hwDeclr()
        self.mask = HwIOVectSignal(self.DATA_WIDTH)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOAddrDataMaskRdVldAgent(sim, self)


class HwIOAddrDataRdVldAgent(HwIODataRdVldAgent):

    @override
    def set_data(self, data):
        i = self.hwIO
        if data is None:
            addr, d = None, None
        else:
            addr, d = data

        i.addr.write(addr)
        i.data.write(d)

    @override
    def get_data(self):
        i = self.hwIO
        return i.addr.read(), i.data.read()


class HwIOAddrDataMaskRdVldAgent(HwIODataRdVldAgent):

    @override
    def set_data(self, data):
        i = self.hwIO
        if data is None:
            addr, d, mask = None, None, None
        else:
            addr, d, mask = data

        i.addr.write(addr)
        i.data.write(d)
        i.mask.write(mask)

    @override
    def get_data(self):
        i = self.hwIO
        return i.addr.read(), i.data.read(), i.mask.read()


class HwIOAddrDataVldAgent(HwIODataRdVldAgent):

    @override
    def set_data(self, data):
        i = self.hwIO
        if data is None:
            addr, d, vld = None, None, None
        else:
            addr, d, vld = data

        i.addr.write(addr)
        i.data.write(d)
        i.vld_flag.write(vld)

    @override
    def get_data(self):
        i = self.hwIO
        return i.addr.read(), i.data.read(), i.vld_flag.read()
