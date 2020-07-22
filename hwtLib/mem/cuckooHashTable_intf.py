from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import VectSignal, HandshakeSync
from hwt.synthesizer.param import Param
from pycocotb.hdlSimulator import HdlSimulator


class CInsertIntf(HandshakeSync):

    def _config(self):
        self.KEY_WIDTH = Param(8)
        self.DATA_WIDTH = Param(0)

    def _declr(self):
        super(CInsertIntf, self)._declr()
        self.key = VectSignal(self.KEY_WIDTH)
        if self.DATA_WIDTH:
            self.data = VectSignal(self.DATA_WIDTH)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = CInsertIntfAgent(sim, self)


class CInsertIntfAgent(HandshakedAgent):
    """
    Agent for CInsertIntf interface
    """

    def __init__(self, sim, intf):
        HandshakedAgent.__init__(self, sim, intf)
        self._hasData = bool(intf.DATA_WIDTH)

    def get_data(self):
        intf = self.intf
        if self._hasData:
            return intf.key.read(), intf.data.read()
        else:
            return intf.key.read()

    def set_data(self, data):
        intf = self.intf
        if self._hasData:
            if data is None:
                k = None
                d = None
            else:
                k, d = data
            return intf.key.write(k), intf.data.write(d)
        else:
            return intf.key.write(data)
