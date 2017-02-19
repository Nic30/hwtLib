from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param
from hwt.interfaces.std import VectSignal, Signal
from hwt.hdlObjects.constants import DIRECTION


class Axi_id(Interface):
    def _config(self):
        self.ID_WIDTH = Param(1)
        
    def _declr(self):
        self.id = VectSignal(self.ID_WIDTH)

class Axi_user(Interface):
    def _config(self):
        self.USER_WIDTH = Param(1)
        
    def _declr(self):
        self.user = VectSignal(self.USER_WIDTH)


class Axi_strb(Interface):
    def _declr(self):
        self.strb = VectSignal(self.DATA_WIDTH // 8)

class Axi_hs(Interface):
    def _declr(self):
        self.ready = Signal(masterDir=DIRECTION.IN)
        self.valid = Signal()    

def AxiMap(prefix, listOfNames, d=None):
    if d is None:
        d = {}
    for n in listOfNames:
        d[n] = (prefix + n).upper()
    return d