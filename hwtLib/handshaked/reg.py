from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.synthetisator.codeOps import If, c

from hwtLib.handshaked.compBase import HandshakedCompBase 

class HandshakedReg(HandshakedCompBase):
    """
    Register for Handshaked interface
    """
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.dataIn = self.intfCls()
                self.dataOut = self.intfCls()
    
    def _impl(self):
        
        isOccupied = self._reg("isOccupied", defVal=0)
        regs_we = self._sig('reg_we')
        
        vld = self.getVld
        rd = self.getRd
        
        m = self.dataOut
        s = self.dataIn

        for iin, iout in zip(self.getData(s), self.getData(m)):
            assert(not iin._interfaces)  # has not subintefraces (Not implemented)
            
            r = self._reg('reg_' + iin._name, iin._dtype)
            
            If(regs_we,
               c(iin, r)
            ).Else(
               r._same()
            )
            c(r, iout)

        If(isOccupied,
            If(rd(m) & ~vld(s),
                c(0, isOccupied)
            ).Else(
                isOccupied._same()
            )
        ).Else(
            If(vld(s),
               c(1, isOccupied)
            ).Else(
               isOccupied._same()
            )
        )
        
        If(isOccupied,
           c(rd(m), rd(s)) + 
           c(1, vld(m)) + 
           c(vld(s), regs_we)
        ).Else(
           c(1, rd(s)) + 
           c(0, vld(m)) + 
           c(vld(s) & rd(m), regs_we)
        )

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    u = HandshakedReg(Handshaked)
    
    print(toRtl(u))
