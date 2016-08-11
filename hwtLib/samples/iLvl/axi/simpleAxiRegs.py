from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.amba import AxiLite
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn
from hdl_toolkit.synthesizer.codeOps import If, c
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hwtLib.axi.axiLite_conv import AxiLiteConverter


class SimpleAxiRegs(Unit):
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.axi = AxiLite()
            self.axi.ADDR_WIDTH.set(8)
            self.axi.DATA_WIDTH.set(32)
        self.conv = AxiLiteConverter([(0, "reg0"),
                                 (4, "reg1")])
        
        
    def _impl(self):
        propagateClkRstn(self)
        c(self.axi, self.conv.bus)
        
        reg0 = self._reg("reg0", vecT(32), defVal=0)
        reg1 = self._reg("reg1", vecT(32), defVal=1)
        
        conv = self.conv
        def connectRegToConveror(convPort, reg):
            If(convPort.dout.vld,
                c(convPort.dout.data, reg)
            ).Else(
                reg._same()
            )
            c(reg, convPort.din)
        
        connectRegToConveror(conv.reg0, reg0)
        connectRegToConveror(conv.reg1, reg1)

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = SimpleAxiRegs()
    print(toRtl(u))
    
