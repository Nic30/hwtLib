from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import VectSignal, HandshakeSync
from hwt.synthesizer.param import Param
from pycocotb.hdlSimulator import HdlSimulator


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
        return i.addr.read(), i.data.read(), i.mask.read()


class AddrDataHs(HandshakeSync):
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        super(AddrDataHs, self)._declr()
        self.addr = VectSignal(self.ADDR_WIDTH)
        self.data = VectSignal(self.DATA_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AddrDataHsAgent(sim, self)


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


class AddrDataBitMaskHs(AddrDataHs):
    def _declr(self):
        super(AddrDataBitMaskHs, self)._declr()
        self.mask = VectSignal(self.DATA_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AddrDataMaskHsAgent(sim, self)
