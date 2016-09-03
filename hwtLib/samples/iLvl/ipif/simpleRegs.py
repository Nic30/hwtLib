from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.ipif import IPIF
from hdl_toolkit.interfaces.utils import addClkRstn, propagateClkRstn
from hdl_toolkit.synthesizer.codeOps import If
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit
from hdl_toolkit.synthesizer.param import Param
from hwtLib.ipif.Ipif_conv import IpifConverter


class SimpleIpifRegs(Unit):
    def _config(self):
        self.ADDR_WIDTH = Param(32)
        self.DATA_WIDTH = Param(32)
        
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():    
                self.ipif = IPIF()
        with self._paramsShared():    
            self.conv = IpifConverter([(0, "reg0"),
                                       (4, "reg1")])
        
        
    def _impl(self):
        propagateClkRstn(self)
        self.conv.bus ** self.ipif
        
        reg0 = self._reg("reg0", vecT(32), defVal=0)
        reg1 = self._reg("reg1", vecT(32), defVal=1)
        
        conv = self.conv
        def connectRegToConveror(convPort, reg):
            If(convPort.dout.vld,
                reg ** convPort.dout.data
            ).Else(
                reg._same()
            )
            convPort.din ** reg
        
        connectRegToConveror(conv.reg0, reg0)
        connectRegToConveror(conv.reg1, reg1)

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    u = SimpleIpifRegs()
    
    
    print(toRtl(u))
    
