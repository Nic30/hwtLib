from hdl_toolkit.hdlObjects.typeShortcuts import vecT, hInt
from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.intfLvl import connect, Param, Unit


class SimpleUnit4(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(16)
        
    def _declr(self):
        dtype = vecT(self.DATA_WIDTH // hInt(8))
        self.a = Signal(dtype=dtype, isExtern=True)
        self.b = Signal(dtype=dtype, isExtern=True)
        
    def _impl(self):
        connect(self.a, self.b)


if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleUnit4()))
