from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param, evalParam
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.interfaces.std import RegCntrl
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthesizer.codeOps import If


class RegArray(Unit):
    def _config(self):
        self.ITEMS = Param(4)
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        with self._asExtern(), self._paramsShared():
            addClkRstn(self)
            self.data = RegCntrl(multipliedBy=self.ITEMS)
    
    def _impl(self):
        regs = self.regs = [self._reg("reg%d" % (i), vecT(self.DATA_WIDTH)) 
                            for i in range(evalParam(self.ITEMS).val)]
        
        for reg, intf in zip(regs, self.data):
            If(intf.dout.vld,
                reg ** intf.dout.data
            )
            
            intf.din ** reg 
        
        

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = RegArray()
    print(toRtl(u))
