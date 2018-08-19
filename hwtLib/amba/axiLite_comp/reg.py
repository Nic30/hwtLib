from hwt.synthesizer.unit import Unit
from hwtLib.amba.axi4Lite import Axi4Lite
from hwt.interfaces.utils import addClkRstn
from hwtLib.amba.axis_comp.builder import AxiSBuilder


class AxiLiteReg(Unit):
    """
    Register for AXI3/4/lite interface
    
    .. hwt-schematic::
    """
    def __init__(self, axiCls=Axi4Lite):
        self._axiCls = axiCls
        super(AxiLiteReg, self).__init__()

    def _config(self):
        self._axiCls._config(self)

    def _declr(self):
        addClkRstn(self)
        with self._paramsShared():
            self.in_s = self._axiCls()
            self.out_m = self._axiCls()._m()

    def _impl(self):
        m = self.out_m
        s = self.in_s

        for src, dst in [(s.ar, m.ar), (s.aw, m.aw), (s.w, m.w),
                         (m.r, s.r), (m.b, s.b)]:
            reg = AxiSBuilder(self, src).buff().end
            dst(reg)


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = AxiLiteReg()
    print(toRtl(u))
