from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn
from hdl_toolkit.synthesizer.codeOps import If, c
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param
from hwtLib.axi.axiLite_conv import AxiLiteConverter
from hwtLib.interfaces.amba import AxiLite
from hwtLib.mem.ram import RamSingleClock


class SimpleAxiRam(Unit):
    def _config(self):
        self.ADDR_WIDTH = Param(16)
        self.DATA_WIDTH = Param(32)
        
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.axi = AxiLite()
            
        with self._paramsShared():
            self.conv = AxiLiteConverter([(0, "reg0"),
                                     (4, "ram0", 512)])
        
        
        self.ram = RamSingleClock()
        self.ram.ADDR_WIDTH.set(9)
        self.ram.DATA_WIDTH.set(self.DATA_WIDTH)
        
    def _impl(self):
        propagateClkRstn(self)
        c(self.axi, self.conv.bus)
        
        reg0 = self._reg("reg0", vecT(32), defVal=0)
        
        conv = self.conv
        If(conv.reg0.dout.vld,
            reg0 ** conv.reg0.dout.data
        ).Else(
            reg0._same()
        )
        conv.reg0.din ** reg0 
        
        self.ram.a ** conv.ram0 

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = SimpleAxiRam()
    print(toRtl(u))
    
