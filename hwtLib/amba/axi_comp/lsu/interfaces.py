from hwt.interfaces.std import Handshaked, VectSignal, Signal
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param
from hwtLib.amba.axi3Lite import Axi3Lite_addr, Axi3Lite_r
from ipCorePackager.constants import DIRECTION
from hwtSimApi.hdlSimulator import HdlSimulator
from hwtLib.amba.axis import AxiStream, AxiStreamAgent


class AxiWriteAggregatorWriteTmpIntf(AxiStream):
    """
    Interface for tmp input register on store buffer write input

    :ivar cam_lookup: VectSignal with value of lookup from item cam
        (1 if cacheline present in store buffer)
    :ivar mask_byte_unaligned: Signal 1 if any byte of mask is 0 or all 1

    .. hwt-autodoc::
    """

    def _config(self):
        AxiStream._config(self)
        self.USE_STRB = True
        self.ADDR_WIDTH = Param(32)
        self.ITEMS = Param(64)

    def _declr(self):
        self.addr = VectSignal(self.ADDR_WIDTH)
        AxiStream._declr(self)
        self.colides_with_last_addr = Signal()
        self.cam_lookup = VectSignal(self.ITEMS)
        self.mask_byte_unaligned = Signal()

    def _initSimAgent(self, sim: HdlSimulator):
        raise NotImplementedError()


class AxiWriteAggregatorReadIntf(Interface):
    """
    An interface which is used to speculatively read data from AxiWriteAggregator

    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.a = Axi3Lite_addr()
        self.r_data_available = Handshaked()
        self.r_data_available.DATA_WIDTH = 1
        self.r = Axi3Lite_r()

    def _initSimAgent(self, sim: HdlSimulator):
        raise NotImplementedError()


class AddrDataIntf(Interface):
    """
    .. hwt-autodoc::
    """

    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(64)

    def _declr(self):
        self.addr = VectSignal(self.ADDR_WIDTH)
        self.data = VectSignal(self.DATA_WIDTH, masterDir=DIRECTION.IN)
