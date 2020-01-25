#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from hwt.interfaces.utils import addClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.amba.axis_comp.builder import AxiSBuilder


@serializeParamsUniq
class AxiBuff(BusBridge):
    """
    Transaction buffer for AXI3/4/Lite and others

    .. hwt-schematic:: _example_AxiBuff
    """

    def __init__(self, intfCls):
        self.intfCls = intfCls
        super(AxiBuff, self).__init__()

    def _config(self):
        self.INTF_CLS = Param(self.intfCls)
        self.intfCls._config(self)
        self.ADDR_BUFF_DEPTH = Param(4)
        self.DATA_BUFF_DEPTH = Param(4)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.m = self.intfCls()

        with self._paramsShared():
            self.s = self.intfCls()._m()

        assert self.ADDR_BUFF_DEPTH > 0 or self.DATA_BUFF_DEPTH > 0, (
            "This buffer is completly dissabled,"
            " it should not be instanciated at all",
            self.ADDR_BUFF_DEPTH, self.DATA_BUFF_DEPTH)

    def _impl(self):
        ADDR_DEPTH = self.ADDR_BUFF_DEPTH
        DATA_DEPTH = self.DATA_BUFF_DEPTH

        for name, m, s, depth in [("ar", self.m.ar, self.s.ar, ADDR_DEPTH),
                                  ("aw", self.m.aw, self.s.aw, ADDR_DEPTH),
                                  ("w", self.m.w, self.s.w, DATA_DEPTH)]:
            i = AxiSBuilder(self, m, name).buff(
                items=depth
            ).end
            s(i)

        for name, m, s, depth in [("r", self.s.r, self.m.r, DATA_DEPTH),
                                  ("b", self.s.b, self.m.b, ADDR_DEPTH)]:
            i = AxiSBuilder(self, m, name).buff(
                items=depth,
            ).end
            s(i)


def _example_AxiBuff():
    from hwtLib.amba.axi4 import Axi4
    u = AxiBuff(Axi4)
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import toRtl
    u = _example_AxiBuff()
    print(toRtl(u))
