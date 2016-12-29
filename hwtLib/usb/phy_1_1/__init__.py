from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.synthesizer.param import Param
from hwt.interfaces.utils import addClkRstn
from hwt.interfaces.std import Signal, Rst

class UsbPhy_1_1(Unit):
    def _config(self):
        self.FREQ = Param(int(60e6))
    
    def _declr(self):
        addClkRstn(self)
        self.phy_tx_mode = Signal() # HIGH level for differential io mode (else single-ended)
        self.usb_rst = Rst()