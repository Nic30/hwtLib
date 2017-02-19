from hwt.synthesizer.param import Param
from hwtLib.amba.axi_intf_common import Axi_hs
from hwt.interfaces.std import VectSignal, Signal
from hwtLib.amba.axi4 import Axi4, Axi4_addr, Axi4_w, Axi4_r, Axi4_b
from hwt.hdlObjects.constants import DIRECTION
from hwtLib.amba.axiLite import AxiLite_bAgent

class AceSnoop_addr(Axi_hs):
    def _config(self):
        self.SNOOP_ADDR_WIDTH = Param(32)
    def _declr(self):
        self.addr = VectSignal(self.ADDR_WIDTH)
        self.snoop = VectSignal(4)
        self.prot = VectSignal(3)
        Axi_hs._declr(self)
    
class AceSnoop_resp(Axi_hs):
    def _declr(self):
        self.resp = VectSignal(4)
        Axi_hs._declr(self)

    def _getSimAgent(self):
        return AxiLite_bAgent

class AceSnoop_data(Axi_hs):
    def _config(self):
        self.SNOOP_DATA_WIDTH = Param(32)

    def _declr(self):
        self.data = VectSignal(self.SNOOP_DATA_WIDTH)
        self.last = Signal()
        Axi_hs._declr(self)

class Ace(Axi4):
    def _config(self):
        Axi4._config(self)
        self.SNOOP_ADDR_WIDTH = Param(32)
        self.SNOOP_DATA_WIDTH = Param(32)
    
    def _declr(self):
        with self._paramsShared():
            self.aw = Axi4_addr()
            self.ar = Axi4_addr()
            self.w = Axi4_w()
            self.r = Axi4_r(masterDir=DIRECTION.IN)
            self.b = Axi4_b(masterDir=DIRECTION.IN)
            
            self.ac = AceSnoop_addr(masterDir=DIRECTION.IN)
            self.cr = AceSnoop_resp()
            self.cd = AceSnoop_data()
            
    def _getIpCoreIntfClass(self):
        raise NotImplementedError()
    