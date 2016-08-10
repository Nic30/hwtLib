from hdl_toolkit.synthesizer.interfaceLevel.interface import Interface
from hwtLib.logic.delayMs import DelayMs
from hdl_toolkit.interfaces.spi import SPI
from hdl_toolkit.interfaces.std import Signal

class Ssd1306Intf(Interface):
    def _config(self):
        DelayMs._config(self)
    
    def _declr(self):
        self.spi = SPI()
        self.dc = Signal()  # Data/Command Pin
        self.res = Signal()  # PmodOLED RES
        self.vbat = Signal()  # VBAT enable
        self.vdd = Signal()  # VDD enable