from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import VectSignal, HandshakeSync
from hwt.synthesizer.param import Param


class AddrDataHsAgent(HandshakedAgent):
    def doWrite(self, s, data):
        i = self.intf
        w = s.write
        if data is None:
            addr, d = None, None
        else:
            addr, d = data

        w(addr, i.addr)
        w(d, i.data)

    def doRead(self, s):
        i = self.intf
        r = s.read
        return r(i.addr), r(i.data), r(i.mask)


class AddrDataHs(HandshakeSync):
    def _config(self):
        self.ADDR_WIDTH = Param(8)
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        super(AddrDataHs, self)._declr()
        self.addr = VectSignal(self.ADDR_WIDTH)
        self.data = VectSignal(self.DATA_WIDTH)

    def _getSimAgent(self):
        return AddrDataHsAgent


class AddrDataMaskHsAgent(HandshakedAgent):
    def doWrite(self, s, data):
        i = self.intf
        w = s.write
        if data is None:
            addr, d, mask = None, None, None
        else:
            addr, d, mask = data

        w(addr, i.addr)
        w(d, i.data)
        w(mask, i.mask)

    def doRead(self, s):
        i = self.intf
        r = s.read
        return r(i.addr), r(i.data), r(i.mask)


class AddrDataBitMaskHs(AddrDataHs):
    def _declr(self):
        super(AddrDataBitMaskHs, self)._declr()
        self.mask = VectSignal(self.DATA_WIDTH)

    def _getSimAgent(self):
        return AddrDataMaskHsAgent
