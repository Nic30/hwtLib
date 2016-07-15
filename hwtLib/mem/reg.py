from hdl_toolkit.intfLvl import connect, Unit
from hdl_toolkit.hdlObjects.types.defs import BIT
from hdl_toolkit.interfaces.std import Rst, Signal, Clk

c = connect

class DReg(Unit):
    def _declr(self):
        with self._asExtern():
            self.clk = Clk()
            self.rst = Rst()
    
            self.din = Signal(dtype=BIT)
            self.dout = Signal(dtype=BIT)
        
        
    def _impl(self):

        internReg = self._reg("internReg", BIT, defVal=False)        
        
        c(self.din, internReg)
        c(internReg, self.dout)
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(DReg))
