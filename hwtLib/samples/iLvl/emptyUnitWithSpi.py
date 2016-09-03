from hdl_toolkit.interfaces.peripheral import Spi
from hdl_toolkit.intfLvl import EmptyUnit 
from hdl_toolkit.synthesizer.shortcuts import toRtl


class EmptyUnitWithSpi(EmptyUnit):
    def _declr(self):
        with self._asExtern():
            self.spi = Spi()
    
    
if __name__ == "__main__":
    print(toRtl(EmptyUnitWithSpi()))
