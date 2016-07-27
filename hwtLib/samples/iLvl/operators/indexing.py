from hdl_toolkit.synthetisator.interfaceLevel.unit import Unit
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.hdlObjects.typeShortcuts import vecT
from hdl_toolkit.synthetisator.codeOps import connect


class SimpleIndexingSplit(Unit):
    def _declr(self):
        with self._asExtern():
            self.a = Signal(dtype=vecT(2))
            self.b = Signal()
            self.c = Signal()
        
    def _impl(self):
        connect(self.a[0], self.b)
        connect(self.a[1], self.c)

class SimpleIndexingJoin(Unit):
    def _declr(self):
        with self._asExtern():
            self.a = Signal(dtype=vecT(2))
            self.b = Signal()
            self.c = Signal()
        
    def _impl(self):
        connect(self.b, self.a[0])
        connect(self.c, self.a[1])




if __name__ == "__main__":  # alias python main function
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(SimpleIndexingJoin))
