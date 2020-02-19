from hwtLib.abstract.busBridge import BusBridge
from hwt.synthesizer.param import Param
from hwt.interfaces.utils import addClkRstn
from hwtLib.amba.axi4Lite import Axi4Lite
from hwt.code import connect


class AxiResize(BusBridge):
    """
    Change DATA_WIDTH of axi interface

    .. hwt-schematic:: _example_AxiResize
    """

    def __init__(self, intfCls):
        self.intfCls = intfCls
        super(AxiResize, self).__init__()

    def _config(self):
        self.INTF_CLS = Param(self.intfCls)
        self.intfCls._config(self)
        self.ALIGN = Param(False)
        self.OUT_DATA_WIDTH = Param(self.DATA_WIDTH)
        self.OUT_ADDR_WIDTH = Param(self.ADDR_WIDTH)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.m = self.intfCls()

        with self._paramsShared():
            self.s = self.intfCls()._m()
            self.s.ADDR_WIDTH = self.OUT_ADDR_WIDTH
            self.s.DATA_WIDTH = self.OUT_DATA_WIDTH

    def _impl(self):
        m, s = self.m, self.s
        has_len = hasattr(s.ar, "len")
        DW = self.DATA_WIDTH
        OUT_DW = self.OUT_DATA_WIDTH
        if DW == OUT_DW and self.ADDR_WIDTH == self.OUT_ADDR_WIDTH:
            raise AssertionError("It is useless to use this convertor"
                                 " if the interface is of same size")

        if has_len:
            # Axi3/4, etc
            if DW <= OUT_DW:
                # always reading/writing less data than is max of output
                raise NotImplementedError()
            else:
                # requires split to multiple transactions on output
                raise NotImplementedError()
        else:
            # Axi4Lite, etc
            if DW <= OUT_DW:
                # always reading/writing less data than is max of output
                if self.ADDR_WIDTH != self.OUT_ADDR_WIDTH:
                    connect(m.aw, s.aw, fit=True)
                    connect(m.ar, s.ar, fit=True)
                else:
                    s.aw(m.aw)
                    s.ar(m.ar)
                connect(m.w, s.w, fit=True)
                connect(s.r, m.r, fit=True)
                m.b(s.b)
            else:
                # requires split to multiple transactions on output
                raise NotImplementedError(DW, OUT_DW)


def _example_AxiResize():
    u = AxiResize(Axi4Lite)
    u.OUT_DATA_WIDTH = 128
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiResize()
    print(toRtl(u))
