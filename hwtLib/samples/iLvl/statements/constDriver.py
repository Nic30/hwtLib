from hdl_toolkit.interfaces.std import Signal
from hdl_toolkit.synthesizer.codeOps import connect
from hdl_toolkit.synthesizer.interfaceLevel.unit import Unit


class ConstDriverUnit(Unit):
    def _declr(self):
        with self._asExtern():
            self.out0 = Signal()
            self.out1 = Signal()
    
    def _impl(self):
        connect(0, self.out0)
        connect(1, self.out1)


if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(ConstDriverUnit()))