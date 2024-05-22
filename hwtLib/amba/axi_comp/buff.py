#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from typing import Optional

from hwt.hwIOs.utils import addClkRstn
from hwt.hwParam import HwParam
from hwt.pyUtils.typingFuture import override
from hwt.serializer.mode import serializeParamsUniq
from hwtLib.abstract.busBridge import BusBridge
from hwtLib.amba.axis_comp.builder import Axi4SBuilder


@serializeParamsUniq
class AxiBuff(BusBridge):
    """
    Transaction buffer for AXI3/4/Lite and others

    .. hwt-autodoc:: _example_AxiBuff
    """

    def __init__(self, hwIOCls, hdlName:Optional[str]=None):
        self.hwIOCls = hwIOCls
        super(AxiBuff, self).__init__(hdlName=hdlName)

    @override
    def hwConfig(self):
        self.HWIO_CLS = HwParam(self.hwIOCls)
        self.hwIOCls.hwConfig(self)
        self.ADDR_BUFF_DEPTH = HwParam(4)
        self.DATA_BUFF_DEPTH = HwParam(4)

    @override
    def hwDeclr(self):
        addClkRstn(self)

        with self._hwParamsShared():
            self.s = self.hwIOCls()

        with self._hwParamsShared():
            self.m = self.hwIOCls()._m()

        assert self.ADDR_BUFF_DEPTH > 0 or self.DATA_BUFF_DEPTH > 0, (
            "This buffer is completely disabled,"
            " it should not be instantiated at all",
            self.ADDR_BUFF_DEPTH, self.DATA_BUFF_DEPTH)

    @override
    def hwImpl(self):
        ADDR_DEPTH = self.ADDR_BUFF_DEPTH
        DATA_DEPTH = self.DATA_BUFF_DEPTH

        for name, m, s, depth in [("ar", self.s.ar, self.m.ar, ADDR_DEPTH),
                                  ("aw", self.s.aw, self.m.aw, ADDR_DEPTH),
                                  ("w", self.s.w, self.m.w, DATA_DEPTH)]:
            i = Axi4SBuilder(self, m, name).buff(
                items=depth
            ).end
            s(i)

        for name, m, s, depth in [("r", self.m.r, self.s.r, DATA_DEPTH),
                                  ("b", self.m.b, self.s.b, ADDR_DEPTH)]:
            i = Axi4SBuilder(self, m, name).buff(
                items=depth,
            ).end
            s(i)


def _example_AxiBuff():
    from hwtLib.amba.axi4 import Axi4
    m = AxiBuff(Axi4)
    return m


if __name__ == "__main__":
    from hwt.synth import to_rtl_str
    m = _example_AxiBuff()
    print(to_rtl_str(m))
