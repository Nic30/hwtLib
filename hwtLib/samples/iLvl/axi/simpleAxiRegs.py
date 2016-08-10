from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.amba import AxiLite
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn
from hdl_toolkit.synthetisator.codeOps import If, c
from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hwtLib.axi.axiLite_regs import AxiLiteRegs


class SimpleAxiRegs(Unit):
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.axi = AxiLite()
            self.axi.ADDR_WIDTH.set(8)
            self.axi.DATA_WIDTH.set(32)
        self.conv = AxiLiteRegs([(0, "reg0"),
                                 (4, "reg1")])
        
        
    def _impl(self):
        propagateClkRstn(self)
        c(self.axi, self.conv.axi)
        
        reg0 = self._reg("reg0", vecT(32), defVal=0)
        reg1 = self._reg("reg1", vecT(32), defVal=1)
        
        conv = self.conv
        If(conv.reg0_out.vld,
            c(conv.reg0_out.data, reg0)
        ).Else(
            reg0._same()
        )
        c(reg0, conv.reg0_in)
        
        If(conv.reg1_out.vld,
            c(conv.reg1_out.data, reg1)
        ).Else(
            reg1._same()
        )
        c(reg1, conv.reg1_in)    

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import (synthesizeAsIpcore, toRtl)
    from hdl_toolkit.serializer.utils import makeTestbenchTemplateFile
    u = SimpleAxiRegs()
    repo = "/home/nic30/Documents/test_ip_repo/"
    synthesizeAsIpcore(u, repo)
    makeTestbenchTemplateFile(u, repo + "SimpleAxiRegs/SimpleAxiRegs_tb.vhd")
    # print(toRtl(u))
    
