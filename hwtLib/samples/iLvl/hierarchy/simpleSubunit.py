from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.intfLvl import Unit
from hwtLib.samples.iLvl.simple import SimpleUnit


class SimpleSubunit(Unit):
    def _declr(self):
        with self._asExtern(): 
            self.a = Signal()
            self.b = Signal()
        
        self.subunit0 = SimpleUnit()

    def _impl(self):
        u = self.subunit0
        u.a ** self.a
        self.b ** u.b
        

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleSubunit()))
