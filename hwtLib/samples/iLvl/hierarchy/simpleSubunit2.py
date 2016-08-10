from hdl_toolkit.hdlObjects.typeShortcuts import hInt
from hdl_toolkit.interfaces.amba import AxiStream
from hdl_toolkit.intfLvl import connect, Unit
from hwtLib.samples.iLvl.simpleAxiStream import SimpleUnitAxiStream


class SimpleSubunit2(Unit):
    def _declr(self):
        self.subunit0 = SimpleUnitAxiStream() 
        self.a0 = AxiStream(isExtern=True)
        self.b0 = AxiStream(isExtern=True)
        
        self.a0.DATA_WIDTH.set(hInt(8))
        self.b0.DATA_WIDTH.set(hInt(8))
    
    def _impl(self):
        u = self.subunit0
        connect(self.a0, u.a)
        connect(u.b, self.b0)

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleSubunit2))
