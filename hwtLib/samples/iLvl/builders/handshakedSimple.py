from hdl_toolkit.intfLvl import Unit
from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.interfaces.utils import addClkRstn

from hwtLib.handshaked.builder import HsBuilder

class HandshakedSimple(Unit):
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.a = Handshaked()
            self.b = Handshaked()
        
    def _impl(self):
        b = HsBuilder(self, self.a)

        b.reg()
        b.fifo(16)
        b.reg()
        
        self.b ** b.end 
        
        

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(HandshakedSimple))
