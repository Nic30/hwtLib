#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.interfaces.utils import addClkRstn
from hwt.serializer.mode import serializeParamsUniq
from hwt.synthesizer.param import Param
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.amba.axis_comp.builder import AxiSBuilder


@serializeParamsUniq
class AxiBuff(BusBridge):
    """
    Transaction buffer for AXI3/4/Lite and others

    .. hwt-autodoc:: _example_AxiBuff
    """

    def __init__(self, intfCls, hdl_name_override:Optional[str]=None):
        self.intfCls = intfCls
        super(AxiBuff, self).__init__(hdl_name_override=hdl_name_override)

    def _config(self):
        self.INTF_CLS = Param(self.intfCls)
        self.intfCls._config(self)
        self.ADDR_BUFF_DEPTH = Param(4)
        self.DATA_BUFF_DEPTH = Param(4)

    def _declr(self):
        addClkRstn(self)

        with self._paramsShared():
            self.s = self.intfCls()

        with self._paramsShared():
            self.m = self.intfCls()._m()

        assert self.ADDR_BUFF_DEPTH > 0 or self.DATA_BUFF_DEPTH > 0, (
            "This buffer is completely disabled,"
            " it should not be instantiated at all",
            self.ADDR_BUFF_DEPTH, self.DATA_BUFF_DEPTH)

    def _impl(self):
        ADDR_DEPTH = self.ADDR_BUFF_DEPTH
        DATA_DEPTH = self.DATA_BUFF_DEPTH

        for name, m, s, depth in [("ar", self.s.ar, self.m.ar, ADDR_DEPTH),
                                  ("aw", self.s.aw, self.m.aw, ADDR_DEPTH),
                                  ("w", self.s.w, self.m.w, DATA_DEPTH)]:
            i = AxiSBuilder(self, m, name).buff(
                items=depth
            ).end
            s(i)

        for name, m, s, depth in [("r", self.m.r, self.s.r, DATA_DEPTH),
                                  ("b", self.m.b, self.s.b, ADDR_DEPTH)]:
            i = AxiSBuilder(self, m, name).buff(
                items=depth,
            ).end
            s(i)


def _example_AxiBuff():
    from hwtLib.amba.axi4 import Axi4
    u = AxiBuff(Axi4)
    return u


if __name__ == "__main__":
    from hwt.synthesizer.utils import to_rtl_str
    u = _example_AxiBuff()
    print(to_rtl_str(u))
