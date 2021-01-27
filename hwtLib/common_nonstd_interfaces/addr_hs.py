from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import HandshakeSync, VectSignal
from hwt.synthesizer.param import Param
from hwtSimApi.hdlSimulator import HdlSimulator


class AddrHs(HandshakeSync):

    def _config(self):
        self.ID_WIDTH = Param(4)
        self.ADDR_WIDTH = Param(32)

    def _declr(self):
        if self.ID_WIDTH:
            self.id = VectSignal(self.ID_WIDTH)
        self.addr = VectSignal(self.ADDR_WIDTH)
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AddrHsAgent(sim, self)


class AddrHsAgent(HandshakedAgent):

    def set_data(self, data):
        i = self.intf
        if data is None:
            id_, addr = None, None
        elif i.ID_WIDTH:
            id_, addr = data
            i.id.write(id_)
        else:
            addr = data

        i.addr.write(addr)

    def get_data(self):
        i = self.intf
        if i.ID_WIDTH:
            return i.id.read(), i.addr.read()
        else:
            return i.addr.read()
