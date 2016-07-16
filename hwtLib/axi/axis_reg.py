from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.amba import AxiStream_withoutSTRB
from hdl_toolkit.synthetisator.rtlLevel.codeOp import If
from hdl_toolkit.synthetisator.rtlLevel.signal.utils import c
from hdl_toolkit.hdlObjects.typeShortcuts import hBit
from hdl_toolkit.interfaces.utils import addClkRstn


class AxiSReg(Unit):
    """
    Register for axi stream interface
    """
    def __init__(self, hsIntfCls):
        """
        @param hsIntfCls: class of interface which should be used as interface of this unit
        """
        assert(issubclass(hsIntfCls, AxiStream_withoutSTRB))
        self.hsIntCls = hsIntfCls
        super().__init__()
        
    def _config(self):
        self.hsIntCls._config(self)
        
    def _declr(self):
        with self._asExtern():
            addClkRstn(self)
            with self._paramsShared():
                self.dataIn = self.hsIntCls()
                self.dataOut = self.hsIntCls()
        
    def _impl(self):
        
        isOccupied = self._reg("isOccupied", defVal=0)
        regs_we = self._sig('reg_we')
        
        
        m = self.dataOut
        s = self.dataIn

        cntrlSigs = [s.valid, s.ready]
        for iin, iout in zip(s._interfaces, m._interfaces):
            if iin not in cntrlSigs:
                assert(not iin._interfaces)  # has not subintefraces
                r = self._reg('reg_' + iin._name, iin._dtype)
                If(regs_we,
                   c(iin, r)
                   ,
                   c(r, r)
                )
                c(r, iout)

        If(isOccupied,
           If(m.ready & ~s.valid,
              c(hBit(0), isOccupied)
              ,
              c(isOccupied, isOccupied)
           )
           ,
           If(s.valid,
              c(hBit(1), isOccupied)
              ,
              c(isOccupied, isOccupied)
           )
        )
        
        If(isOccupied,
           c(m.ready, s.ready) + 
           c(hBit(1), m.valid) + 
           c(s.valid, regs_we)
           ,
           c(hBit(1), s.ready) + 
           c(hBit(0), m.valid) + 
           c(s.valid & m.ready, regs_we)
        )

if __name__ == "__main__":
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    u = AxiSReg(AxiStream_withoutSTRB)
    
    print(toRtl(u))
