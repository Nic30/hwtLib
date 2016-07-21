from hdl_toolkit.intfLvl import connect, Unit
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthetisator.codeOps import Switch

class SimpleUnit(Unit):
    def _declr(self):
        with self._asExtern():
            self.a = Signal()
            self.sel = Signal(dtype=vecT(2))
            self.b = Signal()
            self.c = Signal()
            self.d = Signal()
            
    def _impl(self):
        Switch(self.sel)\
        .Case(0,
            connect(self.b, self.a)
        ).Case(1,
            connect(self.c, self.a)
        ).Case(2,
            connect(self.d, self.a)
        ).Default(
            connect(0, self.a)
        )
        

if __name__ == "__main__": # alias python main function
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleUnit))