from hdl_toolkit.intfLvl import connect, Unit
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.synthetisator.codeOps import If


class SimpleIfStatement(Unit):
    def _declr(self):
        with self._asExtern():
            self.a = Signal()
            self.b = Signal()
            self.c = Signal()
            self.d = Signal()
            
    def _impl(self):
        If(self.a,
           connect(self.b, self.d),
        ).Elif(self.b,
           connect(self.c, self.d)  
        ).Else(
           connect(0, self.d) 
        )

if __name__ == "__main__": # alias python main function
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleIfStatement))