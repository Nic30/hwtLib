from hdl_toolkit.interfaces.amba import AxiStream
from hdl_toolkit.intfLvl import connect, Param, Unit


class SimpleUnitAxiStream(Unit):
    def _config(self):
        self.DATA_WIDTH = Param(8)

    def _declr(self):
        with self._asExtern(), self._paramsShared():
            self.a = AxiStream()
            self.b = AxiStream()

    def _impl(self):
        connect(self.a, self.b)

if __name__ == "__main__":
    from hdl_toolkit.synthesizer.shortcuts import toRtl
    print(toRtl(SimpleUnitAxiStream))
