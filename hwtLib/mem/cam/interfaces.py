from hdl_toolkit.interfaces.std import Ap_hs, s, Ap_vld
from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.hdlObjects.specialValues import DIRECTION



class AddrDataHs(Ap_hs):
    def _config(self):
        Ap_hs._config(self)
        self.ADDR_WIDTH = Param(4)
        
    def _declr(self):
        Ap_hs._declr(self)
        self.addr = s(dtype=vecT(self.ADDR_WIDTH))
        self.mask = s(dtype=vecT(self.DATA_WIDTH))

class CamWritterPort(Ap_vld):
    def _config(self):
        self.COLUMNS = Param(32)
        self.ROWS = Param(1)
        
    def _declr(self):
        self.DATA_WIDTH = self.COLUMNS * 6 
        super()._declr()
        self.di = s(dtype=vecT(self.COLUMNS))
        self.we = s(dtype=vecT(self.ROWS))

class DataWithMatch(Ap_vld):
    def _config(self):
        self.COLUMNS = Param(32)
        self.ROWS = Param(1)
        
    def _declr(self):
        self.DATA_WIDTH = self.COLUMNS * 6 
        super()._declr()
        self.match = s(masterDir=DIRECTION.IN, dtype=vecT(self.ROWS))