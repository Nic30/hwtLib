from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import Handshaked, HandshakeSync, VectSignal
from hwt.synthesizer.param import Param
from pycocotb.hdlSimulator import HdlSimulator


class IndexKeyHs(Handshaked):

    def _config(self):
        self.INDEX_WIDTH = Param(4)
        self.KEY_WIDTH = Param(4)

    def _declr(self):
        HandshakeSync._declr(self)
        self.key = VectSignal(self.KEY_WIDTH)
        self.index = VectSignal(self.INDEX_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = IndexKeyHsAgent(sim, self)


class IndexKeyHsAgent(HandshakedAgent):

    def get_data(self):
        i = self.intf
        return (i.key.read(), i.index.read())

    def set_data(self, data):
        intf = self.intf
        k, i = data
        intf.key.write(k)
        intf.index.write(i)

