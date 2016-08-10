from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.amba import AxiLite
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn
from hdl_toolkit.synthetisator.codeOps import If, c
from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.synthetisator.param import Param
from hwtLib.axi.axiLite_regs import AxiLiteRegs
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
            self.conv = AxiLiteRegs([(0, "reg0"),
                                     (4, "ram0", 512)])
        
        
        self.ram = RamSingleClock()
        self.ram.ADDR_WIDTH.set(9)
        self.ram.DATA_WIDTH.set(self.DATA_WIDTH)
        
    def _impl(self):
        propagateClkRstn(self)
        c(self.axi, self.conv.axi)
        
        reg0 = self._reg("reg0", vecT(32), defVal=0)
        
        conv = self.conv
        If(conv.reg0_out.vld,
            c(conv.reg0_out.data, reg0)
        ).Else(
            reg0._same()
        )
        c(reg0, conv.reg0_in)
        
        c(conv.ram0, self.ram.a)

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import (synthesizeAsIpcore, toRtl)
    from hdl_toolkit.serializer.utils import makeTestbenchTemplateFile
    u = SimpleAxiRam()
    repo = "/home/nic30/Documents/test_ip_repo/"
    synthesizeAsIpcore(u, repo)
    makeTestbenchTemplateFile(u, repo + "SimpleAxiRam/SimpleAxiRam_tb.vhd")
    # print(toRtl(u))
    
