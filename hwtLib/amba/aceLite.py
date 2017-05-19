from hwt.hdlObjects.constants import DIRECTION
from hwt.interfaces.std import VectSignal
from hwtLib.amba.axiLite import AxiLite_addr, AxiLite, AxiLite_w, AxiLite_r, \
    AxiLite_b


#################################################################
class AceLite_addr(AxiLite_addr):
    def _declr(self):
        AxiLite_addr._declr(self)
        self.domain = VectSignal(2)
        self.snoop = VectSignal(3)
        self.bar = VectSignal(2)

    def _getSimAgent(self):
        raise NotImplementedError()
    
class AceLite(AxiLite):
    def _declr(self):
        with self._paramsShared():
            self.aw = AceLite_addr()
            self.ar = AceLite_addr()
            self.w = AxiLite_w()
            self.r = AxiLite_r(masterDir=DIRECTION.IN)
            self.b = AxiLite_b(masterDir=DIRECTION.IN)
            
    def _getIpCoreIntfClass(self):
        raise NotImplementedError()
    
    def _getSimAgent(self):
        raise NotImplementedError()
