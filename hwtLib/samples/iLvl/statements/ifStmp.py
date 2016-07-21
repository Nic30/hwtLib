from hdl_toolkit.intfLvl import connect, Unit
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.synthetisator.codeOps import If


class SimpleIfStatement(Unit):
    def _declr(self):
        with self._asExtern():
            self.a = Signal()
            self.a2 = Signal()
            self.b = Signal()
            self.c = Signal()
            self.d = Signal()
            
    def _impl(self):
        If(self.c,
           connect(self.c, self.a),
           connect(self.c, self.a2)
        ).Elif(self.d,
           connect(self.c, self.a),
           connect(self.c, self.a2)  
        ).Else(
           connect(self.b, self.a)
        )

if __name__ == "__main__": # alias python main function
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleIfStatement))