from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.intfLvl import Unit
from hdl_toolkit.synthesizer.codeOps import If

class SimpleIfStatement(Unit):
    def _declr(self):
        with self._asExtern():
            self.a = Signal()
            self.b = Signal()
            self.c = Signal()
            self.d = Signal()
            
    def _impl(self):
        If(self.a,
           self.d ** self.b,
        ).Elif(self.b,
           self.d ** self.c  
        ).Else(
           self.d ** 0 
        )

if __name__ == "__main__":  # alias python main function
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleIfStatement))
