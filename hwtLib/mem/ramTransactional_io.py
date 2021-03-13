from hwt.interfaces.agents.handshaked import UniversalHandshakedAgent
from hwt.interfaces.agents.universalComposite import UniversalCompositeAgent
from hwt.interfaces.std import HandshakeSync, VectSignal, Signal
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.axis import AxiStream
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION


class TransRamHsR_addr(HandshakeSync):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.ID_WIDTH = Param(0)
        self.ADDR_WIDTH = Param(32)

    def _declr(self):
        if self.ID_WIDTH:
            self.id = VectSignal(self.ID_WIDTH)
        self.addr = VectSignal(self.ADDR_WIDTH)
        HandshakeSync._declr(self)

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = UniversalHandshakedAgent(sim, self)


class TransRamHsW_addr(TransRamHsR_addr):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        TransRamHsR_addr._config(self)
        self.USE_FLUSH = Param(True)

    def _declr(self):
        TransRamHsR_addr._declr(self)
        if(self.USE_FLUSH == True):
            self.flush = Signal()

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = UniversalHandshakedAgent(sim, self)


class TransRamHsR(Interface):
    """
    Handshaked RAM port

    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = Param(8)
        self.USE_STRB = Param(True)
        TransRamHsR_addr._config(self)

    def _declr(self):
        with self._paramsShared():
            self.addr = TransRamHsR_addr()
            d = self.data = AxiStream(masterDir=DIRECTION.IN)
            d.USE_STRB = False
            d.USE_KEEP = False

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = UniversalCompositeAgent(sim, self)


class TransRamHsW(Interface):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = Param(64)
        self.USE_STRB = Param(True)
        TransRamHsW_addr._config(self)

    def _declr(self):
        with self._paramsShared():
            self.addr = TransRamHsW_addr()
            d = self.data = AxiStream()
            d.ID_WIDTH = 0
            d.USE_KEEP = False

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = UniversalCompositeAgent(sim, self)
