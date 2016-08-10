from hdl_toolkit.interfaces.spi import SPI
from hdl_toolkit.intfLvl import EmptyUnit 
from hdl_toolkit.synthesizer.shortcuts import toRtl


class EmptyUnitWithSpi(EmptyUnit):
    def _declr(self):
        self.spi = SPI(isExtern=True)
    
    
if __name__ == "__main__":
    print(toRtl(EmptyUnitWithSpi))
