from hdl_toolkit.bitmask import mask
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.utils import addClkRstn, log2ceil, propagateClkRstn
from hdl_toolkit.synthesizer.codeOps import If, connect
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam
from hwtLib.axi.axiLite_conv import AxiLiteConverter
from hwtLib.interfaces.amba import AxiStream, AxiLite


class AxisFrameGen(Unit):
    """
    Generator of axi stream frames for testing purposes
    """
    def _config(self):
        self.MAX_LEN = Param(511)
        self.CNTRL_AW = Param(4)
        self.CNTRL_DW = Param(32)
        self.DATA_WIDTH = Param(64)
        
    def _declr(self):
        addClkRstn(self)
        self.axis_out = AxiStream()
        self.axis_out.DATA_WIDTH.replace(self.DATA_WIDTH)
        
        self.cntrl = AxiLite()
        self.cntrl.ADDR_WIDTH.set(evalParam(self.CNTRL_AW))
        self.cntrl.DATA_WIDTH.set(evalParam(self.CNTRL_DW))
            
        self.conv = AxiLiteConverter([(0x0, "enable"),
                                      (0x4, "len")
                                     ])
        self.conv.ADDR_WIDTH.set(self.CNTRL_AW)
        self.conv.DATA_WIDTH.set(self.CNTRL_DW)
    
    def _impl(self):
        propagateClkRstn(self)
        cntr = self._reg("wordCntr", vecT(log2ceil(self.MAX_LEN)), defVal=0)
        en = self._reg("enable", defVal=0)
        _len = self._reg("wordCntr", vecT(log2ceil(self.MAX_LEN)), defVal=0)

        self.conv.bus ** self.cntrl 
        cEn = self.conv.enable 
        If(cEn.dout.vld,
           connect(cEn.dout.data, en, fit=True)
        )
        connect(en, cEn.din, fit=True)
        
        cLen = self.conv.len
        If(cLen.dout.vld,
           connect(cLen.dout.data, _len, fit=True)
        )
        connect(_len, cLen.din, fit=True)
        
               
        out = self.axis_out
        connect(cntr, out.data, fit=True)
        out.strb ** mask(self.axis_out.strb._dtype.bit_length())
        out.last ** cntr._eq(0)
        out.valid ** en
        
        If(cLen.dout.vld,
           connect(cLen.dout.data, cntr, fit=True)
        ).Else(
            If(out.ready & en,
               If(cntr._eq(0),
                  cntr ** _len
               ).Else(
                  cntr ** (cntr - 1) 
               )
            )
        )
        


if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = AxisFrameGen()
    print(toRtl(u))
    
    #import os
    #from cli_toolkit.ip_packager.packager import Packager
    #p = Packager(u)
    #p.createPackage(os.path.expanduser("~/Documents/test_ip_repo/")) 
