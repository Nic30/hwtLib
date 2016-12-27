from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param
from hwt.interfaces.std import Handshaked, VldSynced, Signal, VectSignal


class UTMI(Interface):
    """
    USB Transceiver Macrocell Interface 
    """
    def _config(self):
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        with self._paramsShared():
            self.tx = Handshaked()
            self.rx = VldSynced()
        self.rxActivate = Signal()
        self.rxError = Signal()
        self.lineState = VectSignal(2)