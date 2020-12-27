from hwt.hdl.constants import DIRECTION
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream
from hwtSimApi.agents.base import AgentBase
from hwtSimApi.hdlSimulator import HdlSimulator


class AxiStreamFullDuplex(Interface):
    """
    .. hwt-autodoc::
    """
    def _config(self):
        AxiStream._config(self)
        self.HAS_RX = Param(True)
        self.HAS_TX = Param(True)

    def _declr(self):
        with self._paramsShared():
            if self.HAS_TX:
                self.tx = AxiStream()

            if self.HAS_RX:
                self.rx = AxiStream(masterDir=DIRECTION.IN)

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = AxiStreamFullDuplexAgent(sim, self)


class AxiStreamFullDuplexAgent(AgentBase):
    def __init__(self, sim: HdlSimulator, intf: AxiStreamFullDuplex):
        super(AxiStreamFullDuplexAgent, self).__init__(sim, intf)
        if intf.HAS_TX:
            intf.tx._initSimAgent(sim)
        if intf.HAS_RX:
            intf.rx._initSimAgent(sim)

    def getDrivers(self):
        i = self.intf
        d = []
        if i.HAS_TX:
            d.extend(i.tx._ag.getDrivers())
        if i.HAS_RX:
            d.extend(i.rx._ag.getMonitors())
        return d

    def getMonitors(self):
        i = self.intf
        d = []
        if i.HAS_TX:
            d.extend(i.tx._ag.getMonitors())
        if i.HAS_RX:
            d.extend(i.rx._ag.getDrivers())
        return d
