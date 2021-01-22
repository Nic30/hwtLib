from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import Signal, VectSignal
from hwt.math import log2ceil
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param


class LocalLink(Interface):
    """
    Stream with "byte enable" and "start/end of frame/packet"

    .. hwt-autodoc::
    """

    def _config(self):
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        self.rem = VectSignal(log2ceil(self.DATA_WIDTH // 8))
        self.src_rdy_n = Signal()
        self.dst_rdy_n = Signal(masterDir=DIRECTION.IN)
        self.sof_n = Signal()
        self.eof_n = Signal()
        self.eop_n = Signal()
        self.sop_n = Signal()
