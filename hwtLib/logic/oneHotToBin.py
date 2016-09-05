from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.interfaces.utils import log2ceil
from hdl_toolkit.synthesizer.codeOps import If, Or, iterBits
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam


class OneHotToBin(Unit):
    def _config(self):
        self.ONE_HOT_WIDTH = Param(8)
    def _declr(self):
        with self._asExtern():
            self.oneHot = Signal(dtype=vecT(self.ONE_HOT_WIDTH)) 
            self.bin = Signal(dtype=vecT(log2ceil(self.ONE_HOT_WIDTH)))
            self.vld = Signal()
            
    def _impl(self):
        W = evalParam(self.ONE_HOT_WIDTH).val
        
        leadingZeroTop = None  # index is index of first empty record or last one
        for i in reversed(range(W)):
            connections = self.bin ** i
            if leadingZeroTop is None:
                leadingZeroTop = connections 
            else:
                leadingZeroTop = If(self.oneHot[i]._eq(1),
                   connections
                ).Else(
                   leadingZeroTop
                )    
        self.vld ** Or(*[bit for bit in iterBits(self.oneHot)])

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = OneHotToBin()
    print(toRtl(u))  



