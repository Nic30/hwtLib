from hwt.constants import DIRECTION
from hwt.hwIO import HwIO
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwtLib.amba.axi4s import Axi4Stream
from hwtSimApi.agents.base import AgentBase
from hwtSimApi.hdlSimulator import HdlSimulator


class Axi4StreamFullDuplex(HwIO):
    """
    .. hwt-autodoc::
    """

    @override
    def hwConfig(self):
        Axi4Stream.hwConfig(self)
        self.HAS_RX = HwParam(True)
        self.HAS_TX = HwParam(True)

    @override
    def hwDeclr(self):
        with self._hwParamsShared():
            if self.HAS_TX:
                self.tx = Axi4Stream()

            if self.HAS_RX:
                self.rx = Axi4Stream(masterDir=DIRECTION.IN)

    @override
    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = Axi4StreamFullDuplexAgent(sim, self)


class Axi4StreamFullDuplexAgent(AgentBase):

    def __init__(self, sim: HdlSimulator, hwIO: Axi4StreamFullDuplex):
        super(Axi4StreamFullDuplexAgent, self).__init__(sim, hwIO)
        if hwIO.HAS_TX:
            hwIO.tx._initSimAgent(sim)
        if hwIO.HAS_RX:
            hwIO.rx._initSimAgent(sim)

    @override
    def getDrivers(self):
        i = self.hwIO
        if i.HAS_TX:
            yield from i.tx._ag.getDrivers()
        if i.HAS_RX:
            yield from i.rx._ag.getMonitors()

    @override
    def getMonitors(self):
        i = self.hwIO
        if i.HAS_TX:
            yield from i.tx._ag.getMonitors()
        if i.HAS_RX:
            yield from i.rx._ag.getDrivers()
