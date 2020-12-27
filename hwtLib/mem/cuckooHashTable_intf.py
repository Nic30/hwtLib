from hwt.interfaces.agents.handshaked import HandshakedAgent
from hwt.interfaces.std import VectSignal, HandshakeSync, Signal
from hwt.synthesizer.param import Param
from hwtSimApi.hdlSimulator import HdlSimulator


class CInsertIntf(HandshakeSync):
    """
    Cuckoo hash insert interface
    """

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


class CInsertResIntf(CInsertIntf):
    """
    An interface with an result of insert operation.
    
    :ivar pop: signal if 1 the key and data on this interface contains
        the item which had to be removed during insert because the insertion
        limit was exceeded
    """

    def _declr(self):
        self.pop = Signal()
        CInsertIntf._declr(self)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = CInsertResIntfAgent(sim, self)


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
            intf.key.write(k)
            intf.data.write(d)
        else:
            intf.key.write(data)


class CInsertResIntfAgent(CInsertIntfAgent):
    """
    Agent for CInsertResIntf interface
    """

    def get_data(self):
        intf = self.intf
        if self._hasData:
            return intf.pop.read(), intf.key.read(), intf.data.read()
        else:
            return intf.pop.read(), intf.key.read()

    def set_data(self, data):
        intf = self.intf
        if self._hasData:
            if data is None:
                p = None
                k = None
                d = None
            else:
                p, k, d = data
            intf.pop.write(p)
            intf.key.write(k)
            intf.data.write(d)
        else:
            intf.pop.write(p)
            intf.key.write(data)
    
    
