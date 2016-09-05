from hdl_toolkit.hdlObjects.specialValues import Time
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.simulator.shortcuts import simUnitVcd, oscilate, pullUpAfter
from hdl_toolkit.synthesizer.codeOps import If
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.shortcuts import synthesised


class SelfRefCntr(Unit):
    def _declr(self):
        self.dt = vecT(8, False)
        
        with self._asExtern():
            addClkRstn(self)
            
            self.dout = Signal(dtype=self.dt)
            
    def _impl(self):
        cntr = self._reg("cntr", self.dt, defVal=0)
        
        If(cntr._eq(4),
           cntr ** 0
        ).Else(
           cntr ** (cntr + 1)
        )
        
        self.dout ** cntr
        
        
if __name__ == "__main__":
    # print(toRtl(SelfRefCntr()))
    
    u = SelfRefCntr()
    synthesised(u)
    
    simUnitVcd(u, [oscilate(u.clk),
                   pullUpAfter(u.rst_n, intDelay=100)],
                "tmp/selfRefCntr.vcd",
                time=60 * Time.ns)
    print("done")
