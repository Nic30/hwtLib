from hwt.interfaces.std import Signal
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwtLib.interfaces.peripheral import Spi
from hwt.synthesizer.param import Param


class Ssd1306Intf(Interface):
    def _config(self):
        self.FREQ = Param(int(100e6))  # [hz]
        self.MAX_DELAY = Param(100)  # [ms]

    def _declr(self):
        self.spi = Spi()
        self.dc = Signal()  # Data/Command Pin
        self.res = Signal()  # PmodOLED RES
        self.vbat = Signal()  # VBAT enable
        self.vdd = Signal()  # VDD enable
