from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.utils import addClkRstn
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthetisator.codeOps import If, connect

class TwoCntrs(Unit):
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            
            self.a_en = Signal()
            self.b_en = Signal()
            
            self.eq = Signal()
            self.ne = Signal()
            self.lt = Signal()
            self.gt = Signal()
        

    def _impl(self):
        index_t = vecT(8, False)
        
        a = self._reg("reg_a", index_t, defVal=0)
        b = self._reg("reg_b", index_t, defVal=0)
        
        If(self.a_en,
           connect(a+1, a)
        ).Else(
           connect(a, a)
        )
        
        If(self.b_en,
           connect(b+1, b)
        ).Else(
           connect(b, b)
        )
        
        connect(a._eq(b), self.eq)
        connect(a != b, self.ne)
        connect(a < b, self.lt)
        connect(a > b, self.gt)



if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    
    u = TwoCntrs()
    print(toRtl(u))
