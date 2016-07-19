from hdl_toolkit.intfLvl import connect, Unit
from hdl_toolkit.interfaces.std import Handshaked
from hdl_toolkit.interfaces.utils import addClkRstn

from hwtLib.handshaked.builder import HandshakedBuilder

class SimpleSubunit(Unit):
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            self.a = Handshaked()
            self.b = Handshaked()
        
    def _impl(self):
        b = HandshakedBuilder(self, "b", self.a)

        b.reg()
        b.fifo(16)
        b.reg()
        
        connect(b.end, self.b) 
        
        

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    print(toRtl(SimpleSubunit))
