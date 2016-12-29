from hwt.hdlObjects.constants import DIRECTION
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import s
from hwt.code import log2ceil
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param


class FrameLink(Interface):
    def _config(self):
        self.DATA_WIDTH = Param(32)
        
    def _declr(self):
        self.data = s(dtype=vecT(self.DATA_WIDTH))
        self.rem = s(dtype=vecT(log2ceil(self.DATA_WIDTH // 8)))
        self.src_rdy_n = s()
        self.dst_rdy_n = s(masterDir=DIRECTION.IN)
        self.sof_n = s()
        self.eof_n = s()
        self.eop_n = s()
        self.sop_n = s()
