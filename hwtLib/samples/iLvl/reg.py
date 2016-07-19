from hdl_toolkit.intfLvl import c, Unit
from hdl_toolkit.hdlObjects.types.defs import BIT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.interfaces.utils import addClkRst, propagateClkRst

class DReg(Unit):
    def _declr(self):
        with self._asExtern():
            addClkRst(self)
    
            self.din = Signal(dtype=BIT)
            self.dout = Signal(dtype=BIT)
        
        
    def _impl(self):
        internReg = self._reg("internReg", BIT, defVal=False)        
        
        c(self.din, internReg)
        c(internReg, self.dout)

class DoubleDReg(Unit):
    def _declr(self):
        DReg._declr(self)
        
        self.reg0 = DReg()
        self.reg1 = DReg()
    
    def _impl(self):
        propagateClkRst(self)
        
        c(self.din, self.reg0.din)
        c(self.reg0.dout, self.reg1.din)
        c(self.reg1.dout, self.dout)
    
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    u = DoubleDReg()
    print(toRtl(u))
