from hwt.hdl.types.bits import HBits
from hwt.hwIOs.agents.rdVldSync import UniversalRdVldSyncAgent
from hwt.hwIOs.agents.universalComposite import UniversalCompositeAgent
from hwt.hwIOs.std import HwIORdVldSync, HwIOVectSignal, HwIOSignal
from hwt.hwIOs.hwIOStruct import HdlType_to_HwIO
from hwt.hwIO import HwIO
from hwt.hwParam import HwParam
from hwtLib.amba.axi4s import Axi4Stream
from hwtSimApi.hdlSimulator import HdlSimulator
from ipCorePackager.constants import DIRECTION


class TransRamHsR_addr(HwIORdVldSync):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.PRIV_T = HwParam(None)
        self.ADDR_WIDTH = HwParam(32)

    def _declr(self):
        if self.PRIV_T is not None:
            self.priv = HdlType_to_HwIO().apply(self.PRIV_T)
        self.addr = HwIOVectSignal(self.ADDR_WIDTH)
        HwIORdVldSync._declr(self)

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = UniversalRdVldSyncAgent(sim, self)


class TransRamHsW_addr(TransRamHsR_addr):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        TransRamHsR_addr._config(self)
        self.USE_FLUSH = HwParam(True)

    def _declr(self):
        TransRamHsR_addr._declr(self)
        if(self.USE_FLUSH == True):
            self.flush = HwIOSignal()

    def _initSimAgent(self, sim:HdlSimulator):
        self._ag = UniversalRdVldSyncAgent(sim, self)


class TransRamHsR(HwIO):
    """
    Handshaked RAM port

    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = HwParam(8)
        self.USE_STRB = HwParam(True)
        self.ID_WIDTH = HwParam(0)
        self.ADDR_WIDTH = HwParam(32)

    def _declr(self):
        with self._hwParamsShared():
            a = self.addr = TransRamHsR_addr()
            if self.ID_WIDTH:
                a.PRIV_T = HBits(self.ID_WIDTH)
            d = self.data = Axi4Stream(masterDir=DIRECTION.IN)
            d.USE_STRB = False
            d.USE_KEEP = False

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = UniversalCompositeAgent(sim, self)


class TransRamHsW(HwIO):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = HwParam(64)
        self.USE_STRB = HwParam(True)
        TransRamHsW_addr._config(self)

    def _declr(self):
        with self._hwParamsShared():
            self.addr = TransRamHsW_addr()
            d = self.data = Axi4Stream()
            d.ID_WIDTH = 0
            d.USE_KEEP = False

    def _initSimAgent(self, sim: HdlSimulator):
        self._ag = UniversalCompositeAgent(sim, self)
