from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import VectSignal, HandshakeSync, Signal
from hwt.synthesizer.param import Param
from hwtSimApi.hdlSimulator import HdlSimulator


class AddrDataHs(HandshakeSync):
    """
    Simple handshaked interface with address and data signal

    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(8)
        self.HAS_MASK = Param(False)

    def _declr(self):
        super(AddrDataHs, self)._declr()
        self.addr = VectSignal(self.ADDR_WIDTH)
        self.data = VectSignal(self.DATA_WIDTH)
        if self.HAS_MASK:
            assert self.DATA_WIDTH % 8 == 0, self.DATA_WIDTH
            self.mask = VectSignal(self.DATA_WIDTH // 8)

    def _initSimAgent(self, sim: HdlSimulator):
        if self.HAS_MASK:
            self._ag = AddrDataMaskHsAgent(sim, self)
        else:
            self._ag = AddrDataHsAgent(sim, self)


class AddrDataVldHs(AddrDataHs):
    """
    :see: :class:`.AddrDataHs` with a vld_flag signal

    .. hwt-autodoc::
    """

    def _declr(self):
        super(AddrDataVldHs, self)._declr()
        self.vld_flag = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AddrDataVldAgent(sim, self)


class AddrDataBitMaskHs(AddrDataHs):
    """
    :see: :class:`.AddrDataHs` with a mask signal
    :note: mask has 1b granularity

    .. hwt-autodoc::
    """

    def _declr(self):
        super(AddrDataBitMaskHs, self)._declr()
        self.mask = VectSignal(self.DATA_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AddrDataMaskHsAgent(sim, self)


class AddrDataHsAgent(HandshakedAgent):

    def set_data(self, data):
        i = self.intf
        if data is None:
            addr, d = None, None
        else:
            addr, d = data

        i.addr.write(addr)
        i.data.write(d)

    def get_data(self):
        i = self.intf
        return i.addr.read(), i.data.read()


class AddrDataMaskHsAgent(HandshakedAgent):

    def set_data(self, data):
        i = self.intf
        if data is None:
            addr, d, mask = None, None, None
        else:
            addr, d, mask = data

        i.addr.write(addr)
        i.data.write(d)
        i.mask.write(mask)

    def get_data(self):
        i = self.intf
        return i.addr.read(), i.data.read(), i.mask.read()


class AddrDataVldAgent(HandshakedAgent):

    def set_data(self, data):
        i = self.intf
        if data is None:
            addr, d, vld = None, None, None
        else:
            addr, d, vld = data

        i.addr.write(addr)
        i.data.write(d)
        i.vld_flag.write(vld)

    def get_data(self):
        i = self.intf
        return i.addr.read(), i.data.read(), i.vld_flag.read()
