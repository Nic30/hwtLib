from hdl_toolkit.synthetisator.param import Param, evalParam
from hdl_toolkit.interfaces.std import Signal, Handshaked
from hdl_toolkit.hdlObjects.typeShortcuts import vecT, hInt, vec
from hdl_toolkit.synthetisator.codeOps import Switch, c
from hwtLib.handshaked.compBase import HandshakedCompBase

class HandshakedMux(HandshakedCompBase):
    def _config(self):
        self.OUTPUTS = Param(2)
        super()._config()
        
    def _declr(self):
        outputs = evalParam(self.OUTPUTS).val
        
        with self._asExtern():
            self.sel = Signal(dtype=vecT(outputs.bit_length()))
            
            with self._paramsShared():
                self.dataIn = self.intfCls()
                self.dataOut = self.intfCls(multipliedBy=hInt(outputs))
    
    def _impl(self):
        selBits = self.sel._dtype.bit_length()
        In = self.dataIn
        rd = self.getRd
        
        
        for index, outIntf in enumerate(self.dataOut):
            for ini, outi in zip(In._interfaces, outIntf._interfaces):
                if ini == self.getVld(In):
                    c(ini & self.sel._eq(vec(index, selBits)), outi)
                elif ini == rd(In):
                    pass
                    # c(outi, ini)
                else:  # data
                    c(ini, outi)
        Switch(self.sel).addCases(
            [(vec(index, selBits), c(rd(out), rd(In)))
               for index, out in enumerate(self.dataOut) ]
        ) 
        
        
if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    u = HandshakedMux(Handshaked)
    print(toRtl(u))   