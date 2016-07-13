from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.interfaces.std import Ap_none
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import connect
from hdl_toolkit.synthetisator.rtlLevel.codeOp import If
from hdl_toolkit.simulator.shortcuts import simUnitVcd, oscilate, pullUpAfter
from hdl_toolkit.simulator.hdlSimulator import HdlSimulator
from hdl_toolkit.synthetisator.shortcuts import toRtl

class SelfRefCntr(Unit):
    def _declr(self):
        self.dt = vecT(8, False)
        
        with self._asExtern():
            addClkRstn(self)
            
            self.dout = Ap_none(dtype=self.dt)
            
    def _impl(self):
        cntr = self._reg("cntr", self.dt, defVal=0)
        
        If(cntr._eq(4),
           connect(0, cntr)
           ,
           connect(cntr+1, cntr)
        )
        
        connect(cntr, self.dout)
        
        
if __name__ == "__main__":
    print(toRtl(SelfRefCntr()))
    
    u = SelfRefCntr()
    
    simUnitVcd(u, [oscilate(lambda: u.clk),
                   pullUpAfter(lambda: u.rst_n, time =99)],
                "tmp/selfRefCntr.vcd", 
                time=60 * HdlSimulator.ns)
    print("done")