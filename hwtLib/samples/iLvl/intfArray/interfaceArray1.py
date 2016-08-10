from hdl_toolkit.hdlObjects.typeShortcuts import hInt
from hdl_toolkit.interfaces.std import VldSynced
from hdl_toolkit.intfLvl import connect, Unit, Param


class SimpleSubunit(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        with self._asExtern(), self._paramsShared():
            self.c = VldSynced()
            self.d = VldSynced()
        
    def _impl(self):
        connect(self.c, self.d)

class InterfaceArraySample(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)
        
    def _declr(self):
        LEN = hInt(2)
        with self._paramsShared():
            with self._asExtern():
                self.a = VldSynced(multipliedBy=LEN)
                self.b = VldSynced(multipliedBy=LEN)
    
            self.u0 = SimpleSubunit() 
            self.u1 = SimpleSubunit()
            # self.u2 = SimpleSubunit()
        
    def _impl(self):
        
        connect(self.a[0], self.u0.c)
        connect(self.a[1], self.u1.c)
        # u2in = connect(a[2], u2.c)
    
        connect(self.u0.d, self.b[0])
        connect(self.u1.d, self.b[1])
        # u2out = connect(u2.d, b[2])

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(
    toRtl(InterfaceArraySample)
    )
