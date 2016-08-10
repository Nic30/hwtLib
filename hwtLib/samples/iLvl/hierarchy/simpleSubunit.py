from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.intfLvl import connect, Unit
from hwtLib.samples.iLvl.simple import SimpleUnit


class SimpleSubunit(Unit):
    def _declr(self):
        self.subunit0 = SimpleUnit() 
        self.a = Signal(isExtern=True)
        self.b = Signal(isExtern=True)
        
    def _impl(self):
        u = self.subunit0
        connect(self.a, u.a)
        connect(u.b, self.b)
        

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleSubunit))
