from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn
from hdl_toolkit.synthesizer.codeOps import If, c
from hwtLib.handshaked.compBase import HandshakedCompBase 
from hwtLib.handshaked.reg import HandshakedReg


class HandshakedReg2(HandshakedCompBase):
    regCls=HandshakedReg
    """
    Register for Handshaked interface with latency of 2
    
    in->r0->r1->out
    
    two sets of registers
    in.rd = r0 or second set is invalid
    out.vld = r1 is vld
    
    mv r0, r1 if  ~r1vld | out.rd
    
    invalidate r1 if out.rd
    
    LATENCY=2
    DELAY=1
    """
    
    
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.dataIn = self.intfCls()
                self.dataOut = self.intfCls()
                
                self.r0 = self.regCls(self.intfCls)
            
    def _impl(self):
        vld = self.getVld
        rd = self.getRd
        out = self.dataOut
        r0  = self.r0
        
        propagateClkRstn(self)
        c(self.dataIn, r0.dataIn)
        
        wordLoaded = self._reg("wordLoaded", defVal=0)
        If(wordLoaded,
           c(~rd(out), wordLoaded)
        ).Else(
           c(vld(r0.dataOut), wordLoaded)
        )
        
        #r0rd, r0vld =rd(r0.dataOut), vld(r0.dataOut)
        #c(r0.dataOut, self.dataOut, exclude=[r0rd, r0vld])
        for iin, iout in zip(self.getData(r0.dataOut), self.getData(self.dataOut)):
            assert(not iin._interfaces)  # has not subintefraces (Not implemented)
            
            r = self._reg('reg_' + iin._name, iin._dtype)
            
            If(~wordLoaded,
               c(iin, r)
            ).Else(
               r._same()
            )
            c(r, iout)
        
        
        c(~wordLoaded, rd(r0.dataOut))
        c(wordLoaded, vld(out))
        #c(~rReady & vld(r0.dataOut), vld(r1.dataIn))
        #c(rd(r1.dataIn), rReady)
        
        
        
        #c(r1.dataOut, self.dataOut)
       
        
        
if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = HandshakedReg2(Handshaked)
    
    print(toRtl(u))
