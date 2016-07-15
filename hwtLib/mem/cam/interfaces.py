from hdl_toolkit.interfaces.std import Handshaked, s, VldSynced
from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.hdlObjects.specialValues import DIRECTION



class AddrDataHs(Handshaked):
    def _config(self):
        Handshaked._config(self)
        self.ADDR_WIDTH = Param(4)
        
    def _declr(self):
        Handshaked._declr(self)
        self.addr = s(dtype=vecT(self.ADDR_WIDTH))
        self.mask = s(dtype=vecT(self.DATA_WIDTH))

class CamWritterPort(VldSynced):
    def _config(self):
        self.COLUMNS = Param(32)
        self.ROWS = Param(1)
        
    def _declr(self):
        self.DATA_WIDTH = self.COLUMNS * 6 
        super()._declr()
        self.di = s(dtype=vecT(self.COLUMNS))
        self.we = s(dtype=vecT(self.ROWS))

class DataWithMatch(VldSynced):
    def _config(self):
        self.COLUMNS = Param(32)
        self.ROWS = Param(1)
        
    def _declr(self):
        self.DATA_WIDTH = self.COLUMNS * 6 
        super()._declr()
        self.match = s(masterDir=DIRECTION.IN, dtype=vecT(self.ROWS))