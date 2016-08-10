from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.intfLvl import connect, Unit


class SimpleWithNonDirectIntConncetion(Unit):
    def _declr(self):
        self.a = Signal(isExtern=True)
        self.b = Signal()
        self.c = Signal(isExtern=True)
        
    def _impl(self):
        connect(self.a, self.b)
        connect(self.b, self.c)

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleWithNonDirectIntConncetion))
