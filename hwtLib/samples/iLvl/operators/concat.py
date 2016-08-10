from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.synthesizer.codeOps import connect, Concat
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit


class SimpleConcat(Unit):
    def _declr(self):
        with self._asExtern():
            self.a0 = Signal()
            self.a1 = Signal()
            self.a2 = Signal()
            self.a3 = Signal()
    
            self.a_out  = Signal(dtype=vecT(4))
    
    def _impl(self):
        connect(Concat(self.a3, self.a2, self.a1, self.a0), self.a_out)
        

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleConcat))