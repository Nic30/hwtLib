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

class SimpleIndexingRangeJoin(Unit):
    def _declr(self):
        with self._asExtern():
            self.a = Signal(dtype=vecT(4))
            self.b = Signal(dtype=vecT(2))
            self.c = Signal(dtype=vecT(2))
        
    def _impl(self):
        connect(self.b, self.a[2:0])
        connect(self.c, self.a[4:2])

class IndexingInernRangeSplit(Unit):
    def _declr(self):
        with self._asExtern():
            self.a = Signal(dtype=vecT(4))
            self.b = Signal(dtype=vecT(4))
    
    def _impl(self):
        internA = self._sig("internA", vecT(2))
        internB = self._sig("internB", vecT(2))
        
        connect(self.a[2:], internA)
        connect(self.a[:2], internB)
        
        
        connect(internA, self.b[2:])
        connect(internB, self.b[:2])
        

class IndexingInernSplit(Unit):
    def _declr(self):
        with self._asExtern():
            self.a = Signal(dtype=vecT(2))
            self.b = Signal(dtype=vecT(2))
    
    def _impl(self):
        internA = self._sig("internA")
        internB = self._sig("internB")
        
        connect(self.a[0], internA)
        connect(self.a[1], internB)
        
        
        connect(internA, self.b[0])
        connect(internB, self.b[1])
        
class IndexingInernJoin(Unit):
    def _declr(self):
        with self._asExtern():
            self.a = Signal()
            self.b = Signal()
            self.c = Signal()
            self.d = Signal()

    def _impl(self):
        intern = self._sig("internSig", vecT(2))
        
        connect(self.a, intern[0])
        connect(self.b, intern[1])
        
        
        connect(intern[0], self.c)
        connect(intern[1], self.d)
        



if __name__ == "__main__":  # alias python main function
    from hdl_toolkit.synthetisator.shortcuts import toRtl
    # there is more of synthesis methods. toRtl() returns formated vhdl string
    print(toRtl(IndexingInernSplit))
