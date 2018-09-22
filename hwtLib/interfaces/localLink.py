from hwt.code import log2ceil
from hwt.hdl.constants import DIRECTION
from hwt.interfaces.std import s, VectSignal
from hwt.synthesizer.interface import Interface
from hwt.synthesizer.param import Param


class LocalLink(Interface):
    """
    Stream with "byte enable" and "start/end of frame/packet"
    """
    def _config(self):
        self.DATA_WIDTH = Param(32)

    def _declr(self):
        self.data = VectSignal(self.DATA_WIDTH)
        self.rem = VectSignal(log2ceil(self.DATA_WIDTH // 8))
        self.src_rdy_n = s()
        self.dst_rdy_n = s(masterDir=DIRECTION.IN)
        self.sof_n = s()
        self.eof_n = s()
        self.eop_n = s()
        self.sop_n = s()
