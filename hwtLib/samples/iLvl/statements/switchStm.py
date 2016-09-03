from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.intfLvl import Unit
from hdl_toolkit.synthesizer.codeOps import Switch


class SwitchStmUnit(Unit):
    def _declr(self):
        with self._asExtern():
            self.sel = Signal(dtype=vecT(2))
            self.a = Signal()
            self.b = Signal()
            self.c = Signal()
            self.d = Signal()
            
    def _impl(self):
        Switch(self.sel)\
        .Case(0,
            self.a ** self.b
        ).Case(1,
            self.a ** self.c
        ).Case(2,
            self.a ** self.d
        ).Default(
            self.a ** 0
        )
        

if __name__ == "__main__":  # alias python main function
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SwitchStmUnit))
