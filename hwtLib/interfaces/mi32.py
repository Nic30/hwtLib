from hwt.hdlObjects.constants import DIRECTION
from hwt.hdlObjects.typeShortcuts import vecT
from hwt.interfaces.std import s
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param


class Mi32(Interface):
    def _config(self):
        self.DATA_WIDTH = Param(32)
        self.ADDR_WIDTH = Param(32)
        
    def _declr(self):
        self.dwr = s(dtype=vecT(self.DATA_WIDTH))
        self.addr = s(dtype=vecT(self.ADDR_WIDTH))
        self.be = s(dtype=vecT(self.DATA_WIDTH // 8))
        self.rd = s()
        self.wr = s()
        self.ardy = s(masterDir=DIRECTION.IN)
        self.drd = s(dtype=vecT(self.DATA_WIDTH), masterDir=DIRECTION.IN)
        self.drdy = s(masterDir=DIRECTION.IN)
