from hwt.hwIO import HwIO
from hwt.hwIOs.agents.rdVldSync import HwIODataRdVldAgent
from hwt.hwIOs.std import HwIOVectSignal, HwIORdVldSync, HwIOSignal
from hwt.hwParam import HwParam
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION


class HwIOAddrData(HwIO):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = HwParam(32)
        self.DATA_WIDTH = HwParam(64)

    def _declr(self):
        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        self.data = HwIOVectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)


class HwIOAddrDataRdVld(HwIORdVldSync):
    """
    Simple handshaked interface with address and data signal

    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = HwParam(8)
        self.DATA_WIDTH = HwParam(8)
        self.HAS_MASK = HwParam(False)

    def _declr(self):
        super(HwIOAddrDataRdVld, self)._declr()
        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        self.data = HwIOVectSignal(self.DATA_WIDTH)
        if self.HAS_MASK:
            assert self.DATA_WIDTH % 8 == 0, self.DATA_WIDTH
            self.mask = HwIOVectSignal(self.DATA_WIDTH // 8)

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

    def _declr(self):
        super(HwIOAddrDataVldRdVld, self)._declr()
        self.vld_flag = HwIOSignal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOAddrDataVldAgent(sim, self)


class HwIOAddrDataBitMaskRdVld(HwIOAddrDataRdVld):
    """
    :see: :class:`.HwIOAddrDataRdVld` with a mask signal
    :note: mask has 1b granularity

    .. hwt-autodoc::
    """

    def _declr(self):
        super(HwIOAddrDataBitMaskRdVld, self)._declr()
        self.mask = HwIOVectSignal(self.DATA_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = HwIOAddrDataMaskRdVldAgent(sim, self)


class HwIOAddrDataRdVldAgent(HwIODataRdVldAgent):

    def set_data(self, data):
        i = self.hwIO
        if data is None:
            addr, d = None, None
        else:
            addr, d = data

        i.addr.write(addr)
        i.data.write(d)

    def get_data(self):
        i = self.hwIO
        return i.addr.read(), i.data.read()


class HwIOAddrDataMaskRdVldAgent(HwIODataRdVldAgent):

    def set_data(self, data):
        i = self.hwIO
        if data is None:
            addr, d, mask = None, None, None
        else:
            addr, d, mask = data

        i.addr.write(addr)
        i.data.write(d)
        i.mask.write(mask)

    def get_data(self):
        i = self.hwIO
        return i.addr.read(), i.data.read(), i.mask.read()


class HwIOAddrDataVldAgent(HwIODataRdVldAgent):

    def set_data(self, data):
        i = self.hwIO
        if data is None:
            addr, d, vld = None, None, None
        else:
            addr, d, vld = data

        i.addr.write(addr)
        i.data.write(d)
        i.vld_flag.write(vld)

    def get_data(self):
        i = self.hwIO
        return i.addr.read(), i.data.read(), i.vld_flag.read()
