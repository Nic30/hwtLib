from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param
from hdl_toolkit.interfaces.std import Clk, Rst_n, Signal
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthetisator.codeOps import connect, If
from hdl_toolkit.interfaces.utils import binToGray


class GrayCntr(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(4)
        
    def _declr(self):
        with self._asExtern():
            self.clk = Clk() 
            self.rst_n = Rst_n()
            self.en = Signal()

            self.dataOut = Signal(dtype=vecT(self.DATA_WIDTH))
            
    def _impl(self):
        binCntr = self._reg("cntr_bin_reg", self.dataOut._dtype, 1) 
        
        If(self.rst_n._isOn(),
           connect(0, self.dataOut)
           ,
           connect(binToGray(binCntr), self.dataOut)
        )
        
        If(self.en, 
           connect(binCntr +1, binCntr)
           ,
           binCntr._same()
        )

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(GrayCntr))