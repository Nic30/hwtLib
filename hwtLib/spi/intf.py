from hwt.hdlObjects.constants import DIRECTION
from hwt.interfaces.std import Clk, Signal, VectSignal
from hwt.interfaces.tristate import TristateSig
from hwt.synthesizer.interfaceLevel.interface import Interface
from hwt.synthesizer.param import Param


# http://www.corelis.com/education/SPI_Tutorial.htm
class Spi(Interface):
    """
    Bare SPI interface (Serial peripheral interface)
    """
    def _config(self):
        self.SLAVE_CNT = Param(1)

    def _declr(self):
        self.clk = Clk()
        self.mosi = Signal()  # master out slave in
        self.miso = Signal(masterDir=DIRECTION.IN)  # master in slave out
        self.cs = VectSignal(self.SLAVE_CNT)  # chip select
        
        self._associatedClk = self.clk

class SpiTristate(Spi):
    """
    SPI interface where mosi and miso signal are merged into one tristate wire
    """
    def _config(self):
        Spi._config(self)
        self.DATA_WIDTH = Param(1)

    def _declr(self):
        self.clk = Clk()
        with self._paramsShared():
            self.io = TristateSig()  # mosi and miso in one wire
        self.cs = VectSignal(self.SLAVE_CNT)  # chip select
        
        self._associatedClk = self.clk
        

class QSPI(SpiTristate):
    """
    SPI interface with 4 tristate data wires
    """
    def _config(self):
        Spi._config(self)
        self.DATA_WIDTH = Param(4)
